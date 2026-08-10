// The Vite-built PyGWalker application is deliberately reused by the companion extension.
// It is generated before this package is compiled and bundled into the prebuilt extension.
// @ts-ignore -- generated JavaScript lives outside this TypeScript package.
import pygwalkerApp from '../../../pygwalker/templates/dist/pygwalker-app.es.js';

export type IPygWalkerTheme = Record<
  `--${string}`,
  string | number | undefined
>;

export interface IPygWalkerMount {
  unmount: () => void;
  setAppearance: (appearance: 'dark' | 'light') => void;
  setTheme: (theme: IPygWalkerTheme) => void;
}

export interface IPygWalkerApp {
  mountPygWalker: (
    container: HTMLElement,
    props: Record<string, unknown>,
    communication: unknown
  ) => Promise<IPygWalkerMount>;
}

export default pygwalkerApp as IPygWalkerApp;
