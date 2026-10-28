import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {
  ICommandPalette,
  IThemeManager,
  ToolbarButton
} from '@jupyterlab/apputils';
import { INotebookTracker } from '@jupyterlab/notebook';
import { Kernel, KernelMessage } from '@jupyterlab/services';
import { vegaIcon } from '@jupyterlab/ui-components';
import { Message } from '@lumino/messaging';
import { Widget } from '@lumino/widgets';

import pygwalkerApp, {
  IPygWalkerMount,
  IPygWalkerTheme
} from './pygwalker-app';
import { readJupyterTheme } from './theme';


const COMMAND_ID = 'pygwalker:open-sidebar';
const SIDEBAR_ID = 'pygwalker-jupyter-sidebar';
const MAIN_ID = 'pygwalker-jupyter-main';
const COMM_TARGET = 'pygwalker.jupyter.v1';
const PROTOCOL_VERSION = 1;
const NOTEBOOK_APP_NAME = 'Jupyter Notebook';
const BOOTSTRAP_CODE = [
  'from pygwalker.jupyter_extension import ensure_registered as _pygwalker_register_extension',
  '_pygwalker_extension_info = _pygwalker_register_extension()',
  'del _pygwalker_register_extension'
].join('\n');

type JsonObject = Record<string, unknown>;
type Appearance = 'dark' | 'light';

interface IDataFrameInfo {
  name: string;
  rows: number;
  columns: number;
}

interface ICommResponse<T> {
  code: number;
  data: T;
  message: string;
}

interface IHandshake {
  protocolVersion: number;
  coreVersion: string;
  capabilities: string[];
}

interface IListDataFrames {
  dataframes: IDataFrameInfo[];
}

interface IOpenDataFrame {
  protocolVersion: number;
  sessionId: string;
  name: string;
  props: Record<string, unknown>;
}

interface IPendingRequest {
  resolve: (response: ICommResponse<unknown>) => void;
  reject: (error: Error) => void;
  timer: number;
}

class KernelCommClient {
  private readonly pending = new Map<string, IPendingRequest>();
  private readonly endpoints = new Map<
    string,
    (data: unknown) => unknown | Promise<unknown>
  >();
  private disposed = false;

  private constructor(private readonly comm: Kernel.IComm) {
    comm.onMsg = message => {
      this.onMessage(message);
    };
    comm.onClose = () => {
      this.dispose(new Error('The PyGWalker kernel connection closed.'));
    };
  }

  static async connect(kernel: Kernel.IKernelConnection): Promise<KernelCommClient> {
    const comm = kernel.createComm(COMM_TARGET);
    const client = new KernelCommClient(comm);
    // Jupyter comm_open has no shell reply. Awaiting the returned future would leave the
    // sidebar stuck forever; shell-channel ordering guarantees the following handshake is
    // processed after this open message.
    comm.open({ protocolVersion: PROTOCOL_VERSION });
    return client;
  }

  get isDisposed(): boolean {
    return this.disposed;
  }

  async sendMsg<T = unknown>(
    action: string,
    data: JsonObject,
    timeout = 30_000
  ): Promise<ICommResponse<T>> {
    if (this.disposed) {
      throw new Error('The PyGWalker kernel connection is not available.');
    }

    const rid = globalThis.crypto.randomUUID();
    const response = await new Promise<ICommResponse<unknown>>((resolve, reject) => {
      const timer = window.setTimeout(() => {
        this.pending.delete(rid);
        reject(new Error(`PyGWalker kernel request timed out: ${action}`));
      }, timeout);
      this.pending.set(rid, { resolve, reject, timer });
      this.sendRaw(action, data, rid);
    });

    if (response.code !== 0) {
      throw new Error(response.message || `PyGWalker request failed: ${action}`);
    }
    return response as ICommResponse<T>;
  }

  sendMsgAsync(action: string, data: JsonObject, rid: string | null = null): void {
    this.sendRaw(action, data, rid ?? globalThis.crypto.randomUUID());
  }

  registerEndpoint(
    action: string,
    callback: (data: unknown) => unknown | Promise<unknown>
  ): void {
    this.endpoints.set(action, callback);
  }

  dispose(reason = new Error('The PyGWalker kernel connection was disposed.')): void {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    for (const request of this.pending.values()) {
      window.clearTimeout(request.timer);
      request.reject(reason);
    }
    this.pending.clear();
    this.endpoints.clear();
    void this.comm.close();
  }

  private sendRaw(action: string, data: unknown, rid: string): void {
    this.comm.send({
      type: 'pyg_request',
      msg: {
        gid: 'extension',
        rid,
        action,
        data
      }
    } as any);
  }

  private onMessage(message: KernelMessage.ICommMsgMsg): void {
    const payload = message.content.data as {
      type?: string;
      data?: string;
    };
    if (payload.type !== 'pyg_response' || typeof payload.data !== 'string') {
      return;
    }

    const envelope = JSON.parse(payload.data) as {
      rid?: string;
      action: string;
      data: unknown;
    };
    if (envelope.action === 'finish_request') {
      if (!envelope.rid) {
        return;
      }
      const request = this.pending.get(envelope.rid);
      if (!request) {
        return;
      }
      window.clearTimeout(request.timer);
      this.pending.delete(envelope.rid);
      request.resolve(envelope.data as ICommResponse<unknown>);
      return;
    }

    const endpoint = this.endpoints.get(envelope.action);
    if (!endpoint) {
      return;
    }
    Promise.resolve(endpoint(envelope.data)).then(result => {
      if (envelope.rid) {
        this.sendRaw('finish_request', result ?? {}, envelope.rid);
      }
    });
  }
}

class PyGWalkerSidebar extends Widget {
  private readonly refreshButton: HTMLButtonElement;
  private readonly status: HTMLDivElement;
  private readonly list: HTMLUListElement;

  constructor(
    private readonly onRefresh: () => void,
    private readonly onShown: () => void
  ) {
    super();
    this.id = SIDEBAR_ID;
    this.addClass('pygwalker-extension-sidebar');
    this.title.caption = 'Explore a DataFrame with PyGWalker';
    this.title.icon = vegaIcon;

    const heading = document.createElement('h2');
    heading.textContent = 'PyGWalker';

    const intro = document.createElement('p');
    intro.className = 'pygwalker-extension-sidebar-intro';
    intro.textContent =
      'Choose a pandas DataFrame from the active Python notebook kernel.';

    this.refreshButton = document.createElement('button');
    this.refreshButton.className = 'pygwalker-extension-refresh';
    this.refreshButton.type = 'button';
    this.refreshButton.textContent = 'Refresh DataFrames';
    this.refreshButton.addEventListener('click', () => this.onRefresh());

    this.status = document.createElement('div');
    this.status.className = 'pygwalker-extension-status';
    this.status.setAttribute('role', 'status');
    this.status.textContent = 'Open a Python notebook, then refresh.';

    this.list = document.createElement('ul');
    this.list.className = 'pygwalker-extension-list';

    this.node.append(heading, intro, this.refreshButton, this.status, this.list);
  }

  setLoading(message: string): void {
    this.refreshButton.disabled = true;
    this.list.replaceChildren();
    this.setStatus(message, 'normal');
  }

  setError(message: string): void {
    this.refreshButton.disabled = false;
    this.list.replaceChildren();
    this.setStatus(message, 'error');
  }

  setHint(message: string): void {
    this.refreshButton.disabled = false;
    this.list.replaceChildren();
    this.setStatus(message, 'normal');
  }

  setDataFrames(
    dataframes: IDataFrameInfo[],
    onOpen: (dataframe: IDataFrameInfo) => void
  ): void {
    this.refreshButton.disabled = false;
    this.list.replaceChildren();
    if (dataframes.length === 0) {
      this.setStatus(
        'No pandas DataFrames found. Create one in the active kernel and refresh.',
        'normal'
      );
      return;
    }

    this.setStatus(
      `${dataframes.length} pandas DataFrame${dataframes.length === 1 ? '' : 's'} found.`,
      'normal'
    );
    for (const dataframe of dataframes) {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.className = 'pygwalker-extension-dataframe';
      button.type = 'button';
      button.addEventListener('click', () => onOpen(dataframe));

      const name = document.createElement('span');
      name.className = 'pygwalker-extension-dataframe-name';
      name.textContent = dataframe.name;
      const shape = document.createElement('span');
      shape.className = 'pygwalker-extension-dataframe-shape';
      shape.textContent = `${dataframe.rows.toLocaleString()} rows × ${dataframe.columns.toLocaleString()} columns`;
      button.append(name, shape);
      item.append(button);
      this.list.append(item);
    }
  }

  protected onAfterShow(message: Message): void {
    super.onAfterShow(message);
    this.onShown();
  }

  private setStatus(message: string, kind: 'normal' | 'error'): void {
    this.status.textContent = message;
    this.status.dataset.kind = kind;
  }
}

class PyGWalkerMainView extends Widget {
  private appearance: Appearance = 'light';
  private theme: IPygWalkerTheme = {};
  private mount: IPygWalkerMount | null = null;
  private generation = 0;

  constructor() {
    super();
    this.id = MAIN_ID;
    this.addClass('pygwalker-extension-main');
    this.title.icon = vegaIcon;
    this.title.label = 'PyGWalker';
    this.title.caption = 'PyGWalker DataFrame Explorer';
    this.title.closable = true;
  }

  async open(
    name: string,
    props: Record<string, unknown>,
    communication: KernelCommClient
  ): Promise<void> {
    const generation = ++this.generation;
    this.mount?.unmount();
    this.mount = null;
    this.node.replaceChildren();

    const loading = document.createElement('div');
    loading.className = 'pygwalker-extension-main-loading';
    loading.textContent = `Opening ${name}…`;
    this.node.append(loading);

    const host = document.createElement('div');
    host.className = 'pygwalker-extension-main-host';
    const mount = await pygwalkerApp.mountPygWalker(host, props, communication);
    if (this.isDisposed || generation !== this.generation) {
      mount.unmount();
      return;
    }

    this.mount = mount;
    mount.setAppearance(this.appearance);
    mount.setTheme(this.theme);
    this.title.label = `PyGWalker: ${name}`;
    this.node.replaceChildren(host);
  }

  setAppearance(appearance: Appearance): void {
    this.appearance = appearance;
    this.mount?.setAppearance(appearance);
  }

  setTheme(theme: IPygWalkerTheme): void {
    this.theme = theme;
    this.mount?.setTheme(theme);
  }

  dispose(): void {
    ++this.generation;
    this.mount?.unmount();
    this.mount = null;
    super.dispose();
  }
}

class PyGWalkerController {
  private client: KernelCommClient | null = null;
  private kernelId: string | null = null;
  private mainView: PyGWalkerMainView | null = null;
  private refreshGeneration = 0;
  private hasRefreshedVisibleNotebook = false;

  constructor(
    private readonly app: JupyterFrontEnd,
    private readonly tracker: INotebookTracker,
    private readonly sidebar: PyGWalkerSidebar,
    private readonly isNotebook7: boolean,
    private readonly themeManager: IThemeManager | null
  ) {
    tracker.currentChanged.connect(() => {
      this.resetConnection();
      this.hasRefreshedVisibleNotebook = false;
      this.sidebar.setHint('Notebook changed. Refresh to inspect its active kernel.');
      if (this.sidebar.isVisible) {
        void this.refresh();
      }
    });
    themeManager?.themeChanged.connect(() => {
      requestAnimationFrame(() => this.syncMainViewTheme());
    });
  }

  onSidebarShown(): void {
    if (!this.hasRefreshedVisibleNotebook) {
      this.hasRefreshedVisibleNotebook = true;
      void this.refresh();
    }
  }

  async refresh(): Promise<void> {
    const generation = ++this.refreshGeneration;
    this.sidebar.setLoading('Connecting to the active notebook kernel…');
    try {
      const client = await this.getClient();
      const response = await client.sendMsg<IListDataFrames>('list_dataframes', {});
      if (generation !== this.refreshGeneration) {
        return;
      }
      this.sidebar.setDataFrames(response.data.dataframes, dataframe => {
        void this.open(dataframe);
      });
    } catch (error) {
      if (generation !== this.refreshGeneration) {
        return;
      }
      this.sidebar.setError(this.errorMessage(error));
    }
  }

  private async open(dataframe: IDataFrameInfo): Promise<void> {
    this.sidebar.setLoading(`Opening ${dataframe.name} with PyGWalker…`);
    try {
      const client = await this.getClient();
      const response = await client.sendMsg<IOpenDataFrame>('open_dataframe', {
        name: dataframe.name
      });
      if (response.data.protocolVersion !== PROTOCOL_VERSION) {
        throw new Error(
          `Unsupported PyGWalker extension protocol ${response.data.protocolVersion}.`
        );
      }

      const appearance = this.currentAppearance();
      const view = this.ensureMainView();
      view.setAppearance(appearance);
      view.setTheme(readJupyterTheme());
      if (this.isNotebook7) {
        const shell = this.app.shell as typeof this.app.shell & {
          collapseLeft?: () => void;
        };
        shell.collapseLeft?.();
      }
      this.app.shell.activateById(view.id);
      await view.open(
        response.data.name,
        { ...response.data.props, dark: appearance },
        client
      );
      this.sidebar.setHint(
        `${dataframe.name} is open in the PyGWalker work area. Refresh to choose another DataFrame.`
      );
    } catch (error) {
      this.sidebar.setError(this.errorMessage(error));
    }
  }

  private async getClient(): Promise<KernelCommClient> {
    const panel = this.tracker.currentWidget;
    if (!panel) {
      throw new Error('No active notebook. Open a Python notebook and try again.');
    }

    this.sidebar.setLoading('Waiting for the active notebook session…');
    await this.waitFor(
      panel.sessionContext.ready,
      15_000,
      'Timed out waiting for the active notebook session.'
    );
    const kernel = panel.sessionContext.session?.kernel;
    if (!kernel) {
      throw new Error('The active notebook has no running kernel. Start its kernel and retry.');
    }

    if (
      this.client &&
      this.kernelId === kernel.id &&
      !this.client.isDisposed
    ) {
      return this.client;
    }
    // Replace a stale client without invalidating the refresh operation that is creating
    // its replacement. Notebook changes still use the default cancellation behavior.
    this.resetConnection(false);

    this.sidebar.setLoading('Loading the PyGWalker bridge in the kernel…');
    const future = kernel.requestExecute({
      code: BOOTSTRAP_CODE,
      silent: true,
      store_history: false,
      stop_on_error: true
    });
    const reply = await this.waitFor(
      future.done,
      15_000,
      'Timed out while loading the PyGWalker bridge in the kernel.'
    );
    const content = reply.content;
    if (content.status !== 'ok') {
      const detail =
        content.status === 'error'
          ? content.evalue || content.ename
          : 'kernel execution was aborted';
      throw new Error(
        `Kernel could not load the PyGWalker extension bridge: ${detail}`
      );
    }

    this.sidebar.setLoading('Opening the PyGWalker kernel channel…');
    const client = await KernelCommClient.connect(kernel);
    this.sidebar.setLoading('Checking PyGWalker kernel compatibility…');
    const handshake = await client.sendMsg<IHandshake>('extension_handshake', {}, 10_000);
    if (handshake.data.protocolVersion !== PROTOCOL_VERSION) {
      client.dispose();
      throw new Error(
        `PyGWalker core protocol ${handshake.data.protocolVersion} is not supported by this extension.`
      );
    }

    this.client = client;
    this.kernelId = kernel.id;
    return client;
  }

  private async waitFor<T>(
    promise: Promise<T>,
    timeout: number,
    message: string
  ): Promise<T> {
    let timer = 0;
    try {
      return await Promise.race([
        promise,
        new Promise<never>((_, reject) => {
          timer = window.setTimeout(() => reject(new Error(message)), timeout);
        })
      ]);
    } finally {
      window.clearTimeout(timer);
    }
  }

  private ensureMainView(): PyGWalkerMainView {
    if (!this.mainView || this.mainView.isDisposed) {
      this.mainView = new PyGWalkerMainView();
      if (this.isNotebook7) {
        // Notebook 7 has a document-centric shell whose main area accepts only the active
        // notebook. Its native right panel is still resizable and keeps the kernel-backed
        // explorer beside the document without replacing or modifying notebook cells.
        this.app.shell.add(this.mainView, 'right', { rank: 750 });
      } else {
        this.app.shell.add(this.mainView, 'main', { mode: 'split-right' });
      }
    }
    return this.mainView;
  }

  private currentAppearance(): Appearance {
    const theme = this.themeManager?.theme;
    if (theme && this.themeManager) {
      try {
        return this.themeManager.isLight(theme) ? 'light' : 'dark';
      } catch {
        // Fall through to the DOM marker while themes are still being registered.
      }
    }

    const themeLight = document.body.dataset.jpThemeLight;
    if (themeLight === 'true') {
      return 'light';
    }
    if (themeLight === 'false') {
      return 'dark';
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }

  private syncMainViewTheme(): void {
    this.mainView?.setAppearance(this.currentAppearance());
    this.mainView?.setTheme(readJupyterTheme());
  }

  private resetConnection(invalidateRefresh = true): void {
    if (invalidateRefresh) {
      ++this.refreshGeneration;
    }
    this.client?.dispose();
    this.client = null;
    this.kernelId = null;
  }

  private errorMessage(error: unknown): string {
    return error instanceof Error ? error.message : String(error);
  }
}

const plugin: JupyterFrontEndPlugin<void> = {
  id: '@kanaries/pygwalker-jupyter:plugin',
  description: 'Discover pandas DataFrames and open them with PyGWalker.',
  autoStart: true,
  requires: [INotebookTracker],
  optional: [ICommandPalette, IThemeManager],
  activate: (
    app: JupyterFrontEnd,
    tracker: INotebookTracker,
    palette: ICommandPalette | null,
    themeManager: IThemeManager | null
  ): void => {
    const isNotebook7 = app.name === NOTEBOOK_APP_NAME;
    let controller: PyGWalkerController;
    const sidebar = new PyGWalkerSidebar(
      () => {
        void controller.refresh();
      },
      () => controller.onSidebarShown()
    );
    controller = new PyGWalkerController(
      app,
      tracker,
      sidebar,
      isNotebook7,
      themeManager
    );

    app.shell.add(sidebar, 'left', { rank: 750 });
    app.commands.addCommand(COMMAND_ID, {
      label: 'Open PyGWalker DataFrame Explorer',
      caption: 'Discover DataFrames in the active notebook kernel',
      icon: vegaIcon,
      execute: () => {
        app.shell.activateById(sidebar.id);
        controller.onSidebarShown();
      }
    });
    palette?.addItem({ command: COMMAND_ID, category: 'PyGWalker' });

    if (isNotebook7) {
      const addToolbarButton = (panel: INotebookTracker['currentWidget']): void => {
        if (!panel || Array.from(panel.toolbar.names()).includes('pygwalker')) {
          return;
        }
        const button = new ToolbarButton({
          className: 'pygwalker-extension-toolbar-button',
          icon: vegaIcon,
          label: 'PyGWalker',
          tooltip: 'Explore a DataFrame with PyGWalker',
          onClick: () => {
            void app.commands.execute(COMMAND_ID);
          }
        });
        panel.toolbar.insertItem(10, 'pygwalker', button);
        panel.disposed.connect(() => button.dispose());
      };

      tracker.widgetAdded.connect((_, panel) => addToolbarButton(panel));
      tracker.forEach(panel => addToolbarButton(panel));
    }
  }
};

export default plugin;
