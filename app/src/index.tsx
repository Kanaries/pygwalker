import React, { Suspense, useCallback, useContext, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { observer } from "mobx-react-lite";
import { reaction } from "mobx"
import { GraphicWalker, PureRenderer, GraphicRenderer, TableWalker } from '@kanaries/graphic-walker'
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore'
import type { IGWHandler, IViewField, ISegmentKey, IDarkMode, IChatMessage, IRow } from '@kanaries/graphic-walker/interfaces';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib"
import { createRender, useModel } from "@anywidget/react";

import Options from './components/options';
import type {
    IAppProps,
    ICommAskSpecRequest,
    ICommChatChartRequest,
    ICommSaveChartRequest,
} from './interfaces';

import { loadDataSource, postDataService, finishDataService, getDatasFromKernelBySql, getDatasFromKernelByPayload } from './dataSource';

import commonStore from "./store/common";
import { initJupyterCommunication, initHttpCommunication, streamlitComponentCallback, initAnywidgetCommunication } from "./utils/communication";
import communicationStore from "./store/communication"
import { setConfig } from './utils/userConfig';
import type { IPreviewProps, IChartPreviewProps } from './components/preview';
import { Preview, ChartPreview } from './components/preview';
import { getSaveTool } from './tools/saveTool';
import { getExportTool } from './tools/exportTool';
import { getExportDataframeTool } from './tools/exportDataframe';
import { getRuncellTool } from './tools/runcellTool';
import { formatExportedChartDatas } from "./utils/save";
import { tracker } from "@/utils/tracker";
import Notification from "./notify"
import initDslParser from "@kanaries/gw-dsl-parser";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    ToggleGroup,
    ToggleGroupItem,
} from "@/components/ui/toggle-group"
import { SunIcon, MoonIcon, DesktopIcon, ChevronLeftIcon, ChevronRightIcon } from "@radix-ui/react-icons"

// @ts-ignore
import style from './index.css?inline'
import { currentMediaTheme } from './utils/theme';
import { AppContext, darkModeContext } from './store/context';
import FormatSpec from './utils/formatSpec';
import { getOpenDesktopTool } from './tools/openDesktop';
import RuncellBanner from './components/runcellBanner';


const InitModal = React.lazy(() => import("./components/initModal"));
const UploadSpecModal = React.lazy(() => import("./components/uploadSpecModal"));
const UploadChartModal = React.lazy(() => import("./components/uploadChartModal"));
const CodeExportModal = React.lazy(() => import("./components/codeExportModal"));

const ExploreModals = observer((props: {
    exportOpen: boolean;
    setExportOpen: React.Dispatch<React.SetStateAction<boolean>>;
    gwRef: React.MutableRefObject<IGWHandler | null>;
    storeRef: React.MutableRefObject<VizSpecStore | null>;
    setGwIsChanged: React.Dispatch<React.SetStateAction<boolean>>;
    sourceCode: string;
}) => {
    const darkMode = useContext(darkModeContext);

    return (
        <>
            {commonStore.uploadSpecModalOpen && (
                <Suspense fallback={null}>
                    <UploadSpecModal storeRef={props.storeRef} setGwIsChanged={props.setGwIsChanged} />
                </Suspense>
            )}
            {commonStore.uploadChartModalOpen && (
                <Suspense fallback={null}>
                    <UploadChartModal gwRef={props.gwRef} storeRef={props.storeRef} dark={darkMode} />
                </Suspense>
            )}
            {props.exportOpen && (
                <Suspense fallback={null}>
                    <CodeExportModal
                        open={props.exportOpen}
                        setOpen={props.setExportOpen}
                        globalStore={props.storeRef}
                        sourceCode={props.sourceCode}
                    />
                </Suspense>
            )}
        </>
    );
});


const initChart = async (gwRef: React.MutableRefObject<IGWHandler | null>, total: number, props: IAppProps) => {
    if (props.needInitChart && props.env === "jupyter_widgets" && total !== 0) {
        commonStore.setInitModalOpen(true);
        commonStore.setInitModalInfo({
            title: "Recover Charts",
            curIndex: 0,
            total: total,
        });
        for await (const chart of gwRef.current?.exportChartList("data-url")!) {
            const request = await formatExportedChartDatas(chart.data) as ICommSaveChartRequest;
            await communicationStore.comm?.sendMsg("save_chart", request);
            commonStore.setInitModalInfo({
                title: "Recover Charts",
                curIndex: chart.index + 1,
                total: chart.total,
            });
        }
    }
    commonStore.setInitModalOpen(false);
}

const getComputationCallback = (props: IAppProps) => {
    const comm = props.__comm ?? communicationStore.comm;
    if (props.useKernelCalc && props.parseDslType === "client") {
        return getDatasFromKernelBySql(props.fieldMetas, comm);
    }
    if (props.useKernelCalc && props.parseDslType === "server") {
        return getDatasFromKernelByPayload(comm);
    }
}

const MainApp = observer((props: {children: React.ReactNode, darkMode: "dark" | "light" | "media", hideToolBar?: boolean, gid?: string, sendMessage?: boolean}) => {
    const [portal, setPortal] = useState<HTMLDivElement | null>(null);
    const [selectedDarkMode, setSelectedDarkMode] = useState(props.darkMode);
    const [darkMode, setDarkMode] = useState(currentMediaTheme(props.darkMode));

    const sendAppearanceMessageToParent = useCallback((appearance: IDarkMode) => {
        if (!props.sendMessage) return;
        window.parent.postMessage({
            action: "changeAppearance",
            gid: props.gid,
            appearance: appearance
        }, "*");
    }, [props.gid, props.sendMessage]);

    useEffect(() => {
        if (selectedDarkMode === "media") {
            setDarkMode(currentMediaTheme(selectedDarkMode));
            sendAppearanceMessageToParent(currentMediaTheme(selectedDarkMode));
            const media = window.matchMedia('(prefers-color-scheme: dark)');
            const listener = (e: MediaQueryListEvent) => {
                setDarkMode(e.matches ? "dark" : "light");
            }
            media.addEventListener("change", listener);
            return () => media.removeEventListener("change", listener);
        } else {
            sendAppearanceMessageToParent(selectedDarkMode);
            setDarkMode(selectedDarkMode);
        }
    }, [selectedDarkMode])

    return (
        <AppContext
            portalContainerContext={portal}
            darkModeContext={darkMode}
        >
            <div className={`${darkMode === "dark" ? "dark": ""} bg-background text-foreground`}>
                <div className="p-2">
                    <style>{style}</style>
                    <div className='overflow-y-auto'>
                        { props.children }
                    </div>
                    {!props.hideToolBar && (
                        <div className="flex w-full mt-1 p-1 overflow-hidden border-t border-border">
                            <ToggleGroup
                                type="single"
                                value={selectedDarkMode}
                                onValueChange={(value) => {value && setSelectedDarkMode(value as IDarkMode)}}
                            >
                                <ToggleGroupItem value="dark">
                                    <MoonIcon className="h-4 w-4" />
                                </ToggleGroupItem>
                                <ToggleGroupItem value="light">
                                    <SunIcon className="h-4 w-4" />
                                </ToggleGroupItem>
                                <ToggleGroupItem value="media">
                                    <DesktopIcon className="h-4 w-4" />
                                </ToggleGroupItem>
                            </ToggleGroup>
                        </div>
                    )}
                    {commonStore.initModalOpen && (
                        <Suspense fallback={null}>
                            <InitModal />
                        </Suspense>
                    )}
                    <div ref={setPortal}></div>
                </div>
            </div>
        </AppContext>
    )
})

const ExploreApp: React.FC<IAppProps & {initChartFlag: boolean}> = (props) => {
    const gwRef = React.useRef<IGWHandler|null>(null);
    const { userConfig } = props;
    const [exportOpen, setExportOpen] = useState(false);
    const [mode, setMode] = useState<string>("walker");
    const [visSpec, setVisSpec] = useState(props.visSpec);
    const [hideModeOption, _] = useState(true);
    const [isChanged, setIsChanged] = useState(false);
    const storeRef = React.useRef<VizSpecStore|null>(null);
    const disposerRef = React.useRef<(() => void) | undefined>(undefined);
    const storeRefProxied = React.useMemo(
        () =>
            new Proxy(storeRef, {
                set(target, prop, value) {
                    if (prop === "current") {
                        if (value) {
                            disposerRef.current?.();
                            const store = value as VizSpecStore;
                            disposerRef.current = reaction(
                                () => store.currentVis,
                                () => {
                                    setIsChanged((value as VizSpecStore).canUndo);
                                    streamlitComponentCallback({
                                        event: "spec_change",
                                        data: store.exportCode()
                                    });
                                },
                            );
                        }
                    }
                    return Reflect.set(target, prop, value);
                },
            }),
        []
    );

    commonStore.setVersion(props.version!);

    useEffect(() => {
        commonStore.setShowCloudTool(props.showCloudTool);
        tracker.setUserId(props.hashcode ?? "");
        if (userConfig) {
            setConfig(userConfig);
            tracker.setOpen(userConfig.privacy === "events");
        };
    }, [props.showCloudTool, props.hashcode, userConfig]);

    useEffect(() => {
        setVisSpec(props.visSpec);
    }, [props.visSpec]);

    useEffect(() => {
        if (props.initChartFlag) {
            setTimeout(() => { initChart(gwRef, visSpec.length, props) }, 0);
        }
    }, [props.initChartFlag, props.id, props.visSpec, visSpec.length]);

    useEffect(() => {
        setTimeout(() => {
            storeRef.current?.setSegmentKey(props.defaultTab as ISegmentKey);
        }, 0);
    }, [mode, props.defaultTab]);

    const runcellTool = getRuncellTool();
    const exportTool = getExportTool(setExportOpen);
    const openInDesktopTool = getOpenDesktopTool(props, storeRef);

    const tools = [runcellTool, exportTool, openInDesktopTool];
    if (props.env && ["jupyter_widgets", "streamlit", "gradio", "marimo", "anywidget", "web_server"].indexOf(props.env) !== -1 && props.useSaveTool) {
        const saveTool = getSaveTool(props, gwRef, storeRef, isChanged, setIsChanged);
        tools.push(saveTool);
    }
    if (props.isExportDataFrame) {
        const exportDataFrameTool = getExportDataframeTool(props, storeRef);
        tools.push(exportDataFrameTool);
    }

    const toolbarConfig = {
        exclude: ["export_code"],
        extra: tools
    }

    const enhanceAPI = React.useMemo(() => {
        if (props.showCloudTool) {
            const features: Record<string, any> = {};
            if (props.enableAskViz) {
                features["askviz"] = async (metas: IViewField[], query: string) => {
                    const request: ICommAskSpecRequest = { metas, query };
                    const resp = await communicationStore.comm?.sendMsg("get_spec_by_text", request);
                    return resp?.data?.data;
                };
            }
            if (props.enableVlChat) {
                features["vlChat"] = async (metas: IViewField[], chats: IChatMessage[]) => {
                    const request: ICommChatChartRequest = { metas, chats };
                    const resp = await communicationStore.comm?.sendMsg("get_chart_by_chats", request);
                    return resp?.data?.data;
                };
            }
            if (Object.keys(features).length > 0) {
                return { features };
            }
        }
        return undefined;
    }, [props.showCloudTool, props.enableAskViz, props.enableVlChat]);

    const computationCallback = React.useMemo(
        () => getComputationCallback(props),
        [props.useKernelCalc, props.parseDslType, props.fieldMetas, props.__comm],
    );

    const modeChange = (value: string) => {
        if (mode === "walker") {
            setVisSpec(storeRef.current?.exportCode());
        }
        setMode(value);
    }
  
    return (
        <React.StrictMode>
            <Notification />
            <ExploreModals
                exportOpen={exportOpen}
                setExportOpen={setExportOpen}
                gwRef={gwRef}
                storeRef={storeRef}
                setGwIsChanged={setIsChanged}
                sourceCode={props["sourceInvokeCode"] || ""}
            />
            {
                !hideModeOption &&
                <Select onValueChange={modeChange} defaultValue='walker' >
                    <SelectTrigger className="w-[140px] h-[30px] mb-[20px] text-xs">
                        <span className='text-muted-foreground'>Mode: </span>
                        <SelectValue className='' placeholder="Mode" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="walker">Walker</SelectItem>
                        <SelectItem value="renderer">Renderer</SelectItem>
                    </SelectContent>
                </Select>
            }
            {
                mode === "walker" ? 
                <GraphicWalker
                    {...props.extraConfig}
                    appearance={useContext(darkModeContext)}
                    vizThemeConfig={props.themeKey}
                    fieldkeyGuard={props.fieldkeyGuard}
                    fields={props.rawFields}
                    data={props.useKernelCalc ? undefined : props.dataSource}
                    storeRef={storeRefProxied}
                    ref={gwRef}
                    toolbar={toolbarConfig}
                    computation={computationCallback}
                    enhanceAPI={enhanceAPI}
                    chart={visSpec.length === 0 ? undefined : visSpec}
                    experimentalFeatures={{ computedField: props.useKernelCalc }}
                    defaultConfig={{ config: { timezoneDisplayOffset: 0 } }}
                /> :
                <GraphicRendererApp
                    {...props}
                    dataSource={props.dataSource}
                    visSpec={visSpec}
                />
            }
            <Options {...props} />
        </React.StrictMode>
    );
}

const PureRednererApp: React.FC<IAppProps> = observer((props) => {
    const computationCallback = getComputationCallback(props);
    const spec = props.visSpec[0];
    const [expand, setExpand] = useState(false);

    return (
        <React.StrictMode>
            <div className='flex'>
                {
                    !expand && (
                        props.useKernelCalc ?
                        <PureRenderer
                            {...props.extraConfig}
                            appearance={useContext(darkModeContext)}
                            vizThemeConfig={props.themeKey}
                            name={spec.name}
                            visualConfig={spec.config}
                            visualLayout={spec.layout}
                            visualState={spec.encodings}
                            type='remote'
                            computation={computationCallback!}
                        /> :
                        <PureRenderer
                            {...props.extraConfig}
                            appearance={useContext(darkModeContext)}
                            vizThemeConfig={props.themeKey}
                            name={spec.name}
                            visualConfig={spec.config}
                            visualLayout={spec.layout}
                            visualState={spec.encodings}
                            rawData={props.dataSource}
                        />
                    )
                }
                {
                    expand && commonStore.isStreamlitComponent && (
                        <div style={{minWidth: "96%"}}>
                            <GraphicWalker
                                {...props.extraConfig}
                                appearance={useContext(darkModeContext)}
                                vizThemeConfig={props.themeKey}
                                fieldkeyGuard={props.fieldkeyGuard}
                                fields={props.rawFields}
                                data={props.useKernelCalc ? undefined : props.dataSource}
                                computation={computationCallback}
                                chart={props.visSpec}
                                experimentalFeatures={{ computedField: props.useKernelCalc }}
                                defaultConfig={{ config: { timezoneDisplayOffset: 0 } }}
                            />
                        </div>
                    )
                }
                { commonStore.isStreamlitComponent && expand && ( <ChevronLeftIcon className='h-6 w-6 cursor-pointer border border-black-600 rounded-full'onClick={() => setExpand(false)}></ChevronLeftIcon> )}
                { commonStore.isStreamlitComponent && !expand && ( <ChevronRightIcon className='h-6 w-6 cursor-pointer border border-black-600 rounded-full'onClick={() => setExpand(true)}></ChevronRightIcon> )}
            </div>
        </React.StrictMode>
    )
});

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

function GWalkerComponent(props: IAppProps) {
    const [initChartFlag, setInitChartFlag] = useState(false);
    const [dataSource, setDataSource] = useState<IRow[]>(props.dataSource);

    useEffect(() => {
        let cancelled = false;
        setInitChartFlag(false);
        if (props.needLoadDatas) {
            loadDataSource(props.dataSourceProps).then((data) => {
                if (cancelled) return;
                setDataSource(data);
                setInitChartFlag(true);
                commonStore.setInitModalOpen(false);
            })
        } else {
            setDataSource(props.dataSource);
            setInitChartFlag(true);
        }
        return () => {
            cancelled = true;
        }
    }, [props.needLoadDatas, props.dataSource, props.dataSourceProps.dataSourceId, props.dataSourceProps.tunnelId]);

    return (
        <React.StrictMode>
            <RuncellBanner env={props.env} />
            { props.gwMode === "explore"  && <ExploreApp {...props} dataSource={dataSource} initChartFlag={initChartFlag} /> }
            { props.gwMode === "renderer" && <PureRednererApp {...props} dataSource={dataSource}  /> }
            { props.gwMode === "filter_renderer" && <GraphicRendererApp {...props} dataSource={dataSource} /> }
            { props.gwMode === "table" && <TableWalkerApp {...props} dataSource={dataSource} /> }
        </React.StrictMode>
    )
}

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

function GraphicRendererApp(props: IAppProps) {
    const computationCallback = getComputationCallback(props);
    const containerSize = props["containerSize"] ?? [null, null];
    const globalProps = {
        rawFields: props.rawFields,
        containerStyle: {
            height: containerSize[1] ? `${containerSize[1]-200}px` : "700px",
            width: containerSize[0] ? `${containerSize[0]-20}px` : "60%"
        },
        themeKey:props.themeKey,
        dark: useContext(darkModeContext),
    }

    return (
        <React.StrictMode>
            <Tabs defaultValue="0" className="w-full">
                <div className="overflow-x-auto max-w-full">
                    <TabsList>
                        {props.visSpec.map((chart, index) => {
                            return <TabsTrigger key={index} value={index.toString()}>{chart.name}</TabsTrigger>
                        })}
                    </TabsList>
                </div>
                {props.visSpec.map((chart, index) => {
                    return <TabsContent key={index} value={index.toString()}>
                        {
                            props.useKernelCalc ? 
                            <GraphicRenderer
                                {...globalProps}
                                computation={computationCallback!}
                                chart={[chart]}
                            /> :
                            <GraphicRenderer
                                {...globalProps}
                                data={props.dataSource!}
                                chart={[chart]}
                            />
                        }
                    </TabsContent>
                })}
            </Tabs>
        </React.StrictMode>
    )
}

function TableWalkerApp(props: IAppProps) {
    const computationCallback = getComputationCallback(props);
    const globalProps = {
        rawFields: props.rawFields,
        themeKey: props.themeKey,
        dark: useContext(darkModeContext)
    }

    return (
        <React.StrictMode>
            {
                props.useKernelCalc ?
                <TableWalker
                    {...globalProps}
                    computation={computationCallback!}
                /> :
                <TableWalker
                    {...globalProps}
                    data={props.dataSource}
                />
            }
        </React.StrictMode>
    )
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


export default { GWalker, PreviewApp, ChartPreviewApp, StreamlitGWalker, render: createRender(AnywidgetGWalkerApp) }
