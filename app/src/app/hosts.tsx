import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Streamlit, withStreamlitConnection } from 'streamlit-component-lib';
import { useModel } from '@anywidget/react';
import initDslParser from '@kanaries/gw-dsl-parser';
import type { IAppProps } from '../interfaces';
import type { IPreviewProps, IChartPreviewProps } from '../components/preview';
import { Preview, ChartPreview } from '../components/preview';
import { postDataService, finishDataService } from '../dataSource';
import commonStore from '../store/common';
import communicationStore from '../store/communication';
import { initJupyterCommunication, initHttpCommunication, initAnywidgetCommunication } from '../utils/communication';
import type { ICommunication } from '../utils/communication';
import FormatSpec from '../utils/formatSpec';
import { currentMediaTheme, hostThemeToUITheme } from '../utils/theme';
import { MainApp, hostContainerContext } from './shell';
import type { IPygWalkerTheme } from './shell';
import { GWalkerComponent } from './views';

const initOnJupyter = async(props: IAppProps) => {
    const comm = initJupyterCommunication(props.id);
    comm.registerEndpoint("postData", postDataService);
    comm.registerEndpoint("finishData", finishDataService);
    props.__comm = comm;
    communicationStore.setComm(comm);
    if (props.needLoadLastSpec) {
        const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
        props.visSpec = FormatSpec(visSpecResp.data?.visSpec ?? [], props.rawFields);
    }
    if (props.needLoadDatas) {
        comm.sendMsgAsync("request_data", {}, null);
    }
    await initDslParser();
}

const initOnHttpCommunication = async(props: IAppProps) => {
    const comm = await initHttpCommunication(props.id, props.communicationUrl);
    props.__comm = comm;
    communicationStore.setComm(comm);
    if ((props.gwMode === "explore" || props.gwMode === "filter_renderer") && props.needLoadLastSpec) {
        const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
        props.visSpec = visSpecResp.data?.visSpec ?? [];
    }
    await initDslParser();
}

const initOnAnywidgetCommunication = async(props: IAppProps, model: import("@anywidget/types").AnyModel) => {
    const comm = await initAnywidgetCommunication(props.id, model);
    props.__comm = comm;
    communicationStore.setComm(comm);
    if ((props.gwMode === "explore" || props.gwMode === "filter_renderer") && props.needLoadLastSpec) {
        const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
        props.visSpec = visSpecResp.data?.visSpec ?? [];
    }
    await initDslParser();
}

const defaultInit = async(props: IAppProps) => {}

const formatAppProps = (props: IAppProps): IAppProps => ({
    ...props,
    id: String(props.id),
    visSpec: FormatSpec(props.visSpec, props.rawFields),
});

function GWalker(props: IAppProps, id: string) {
    props.visSpec = FormatSpec(props.visSpec, props.rawFields);
    let preRender = defaultInit;
    switch(props.env) {
        case "jupyter_widgets":
            preRender = initOnJupyter;
            break;
        case "streamlit":
            preRender = initOnHttpCommunication;
            break;
        case "gradio":
            preRender = initOnHttpCommunication;
            break;
        case "web_server":
            preRender = initOnHttpCommunication;
            break;
        default:
            preRender = defaultInit;
    }

    preRender(props).then(() => {
        const container = document.getElementById(id);
        if (container) {
            createRoot(container).render(
                <MainApp darkMode={props.dark} gid={props.id} sendMessage={props.env?.startsWith("jupyter")}>
                    <GWalkerComponent {...props} />
                </MainApp>
            );
        }
    })
}

function PreviewApp(props: IPreviewProps, containerId: string) {
    props.charts = FormatSpec(props.charts.map(chart => chart.visSpec), [])
                    .map((visSpec, index) => { return {...props.charts[index], visSpec} });

    if (window.document.getElementById(`gwalker-${props.gid}`)) {
        window.document.getElementById(containerId)?.remove();
    }

    const container = document.getElementById(containerId);
    if (container) {
        createRoot(container).render(
            <MainApp darkMode={props.dark} hideToolBar>
                <Preview {...props} />
            </MainApp>
        );
    }
}

function ChartPreviewApp(props: IChartPreviewProps, id: string) {
    props.visSpec = FormatSpec([props.visSpec], [])[0];
    const container = document.getElementById(id);
    if (container) {
        createRoot(container).render(
            <MainApp darkMode={props.dark} hideToolBar>
                <ChartPreview {...props} />
            </MainApp>
        );
    }
}

function SteamlitGWalkerApp(streamlitProps: any) {
    const props = React.useMemo(
        () => formatAppProps(streamlitProps.args as IAppProps),
        [streamlitProps.args],
    );
    const [inited, setInited] = useState(false);
    const container = React.useRef<HTMLDivElement>(null);

    useEffect(() => {
        commonStore.setIsStreamlitComponent(true);
        let cancelled = false;
        setInited(false);
        initOnHttpCommunication(props).then(() => {
            if (cancelled) return;
            setInited(true);
        })
        return () => {
            cancelled = true;
        }
    }, [props.id, props.communicationUrl]);

    useEffect(() => {
        if (!container.current) return;
        const resizeObserver = new ResizeObserver(() => {
            Streamlit.setFrameHeight((container.current?.clientHeight  ?? 0) + 20);
        })
        resizeObserver.observe(container.current);
        return () => resizeObserver.disconnect();
    }, [inited]);

    return (
        <React.StrictMode>
            {inited && (
                <div ref={container}>
                    <MainApp darkMode={props.dark}>
                        <GWalkerComponent {...props} />
                    </MainApp>
                </div>
            )}
        </React.StrictMode>
    );
};

const StreamlitGWalker = () => {
    const StreamlitGWalkerComponent = withStreamlitConnection(SteamlitGWalkerApp);
    const container = document.getElementById("root");
    if (container) {
        createRoot(container).render(
            <React.StrictMode>
                <StreamlitGWalkerComponent />
            </React.StrictMode>
        );
    }
}

function AnywidgetGWalkerApp() {
    const [inited, setInited] = useState(false);
    const model = useModel();
    const propsRef = React.useRef<IAppProps | null>(null);
    if (!propsRef.current) {
        propsRef.current = JSON.parse(model.get("props")) as IAppProps;
        propsRef.current.visSpec = FormatSpec(propsRef.current.visSpec, propsRef.current.rawFields);
    }
    const props = propsRef.current;

    useEffect(() => {
        initOnAnywidgetCommunication(props, model).then(() => {
            setInited(true);
        })
    }, []);

    return (
        <React.StrictMode>
            {!inited && <div>Loading...</div>}
            {inited && (
                <MainApp darkMode={props.dark}>
                    <GWalkerComponent {...props} />
                </MainApp>
            )}
        </React.StrictMode>
    );
}

export interface IPygWalkerMount {
    unmount: () => void;
    setAppearance: (appearance: "dark" | "light") => void;
    setTheme: (theme: IPygWalkerTheme) => void;
}

/**
 * Mount the existing PyGWalker application with a host-provided communication adapter.
 *
 * The JupyterLab companion extension uses this boundary instead of pretending to be an
 * anywidget. The returned handle can update the host appearance without remounting the
 * explorer. Round 1 intentionally allows one such mount at a time because the legacy app
 * stores are module-level singletons.
 */
async function mountPygWalker(
    container: HTMLElement,
    inputProps: IAppProps,
    comm: ICommunication,
): Promise<IPygWalkerMount> {
    const props = formatAppProps({
        ...inputProps,
        env: "jupyter_extension",
        __comm: comm,
    });

    communicationStore.setComm(comm);
    if ((props.gwMode === "explore" || props.gwMode === "filter_renderer") && props.needLoadLastSpec) {
        const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
        props.visSpec = visSpecResp.data?.visSpec ?? [];
    }
    await initDslParser();

    // Tailwind's preflight and the app's base styles must stay inside the host pane.
    const root = createRoot(container.shadowRoot ?? container.attachShadow({ mode: "open" }));
    let appearance = currentMediaTheme(props.dark);
    let theme: IPygWalkerTheme | undefined;
    const render = () => {
        root.render(
            <hostContainerContext.Provider value={container}>
                <MainApp darkMode={appearance} theme={theme} hideToolBar>
                    <GWalkerComponent
                        {...props}
                        extraConfig={theme ? {
                            ...props.extraConfig,
                            uiTheme: hostThemeToUITheme(theme),
                        } : props.extraConfig}
                    />
                </MainApp>
            </hostContainerContext.Provider>
        );
    };
    render();

    return {
        unmount: () => root.unmount(),
        setAppearance: nextAppearance => {
            if (appearance === nextAppearance) {
                return;
            }
            appearance = nextAppearance;
            render();
        },
        setTheme: nextTheme => {
            theme = { ...nextTheme };
            render();
        },
    };
}

export { GWalker, PreviewApp, ChartPreviewApp, StreamlitGWalker, AnywidgetGWalkerApp, mountPygWalker };
