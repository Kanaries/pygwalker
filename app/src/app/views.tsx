import React, { Suspense, useContext, useEffect, useState } from 'react';
import { observer } from 'mobx-react-lite';
import { reaction } from 'mobx';
import { GraphicWalker, PureRenderer, GraphicRenderer, TableWalker } from '@kanaries/graphic-walker';
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore';
import type { IGWHandler, IViewField, ISegmentKey, IChatMessage, IRow } from '@kanaries/graphic-walker/interfaces';
import { ChevronLeftIcon, ChevronRightIcon } from '@radix-ui/react-icons';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import Options from '../components/options';
import RuncellBanner from '../components/runcellBanner';
import type { IAppProps, ICommAskSpecRequest, ICommChatChartRequest, ICommSaveChartRequest } from '../interfaces';
import { loadDataSource, getDatasFromKernelBySql, getDatasFromKernelByPayload } from '../dataSource';
import commonStore from '../store/common';
import communicationStore from '../store/communication';
import { darkModeContext } from '../store/context';
import { streamlitComponentCallback } from '../utils/communication';
import { setConfig } from '../utils/userConfig';
import { formatExportedChartDatas } from '../utils/save';
import { tracker } from '../utils/tracker';
import { getSaveTool } from '../tools/saveTool';
import { getExportTool } from '../tools/exportTool';
import { getExportDataframeTool } from '../tools/exportDataframe';
import { getRuncellTool } from '../tools/runcellTool';
import { getOpenDesktopTool } from '../tools/openDesktop';
import Notification from '../notify';
import { HostShadowSlot } from './shell';

const UploadSpecModal = React.lazy(() => import("../components/uploadSpecModal"));
const UploadChartModal = React.lazy(() => import("../components/uploadChartModal"));
const CodeExportModal = React.lazy(() => import("../components/codeExportModal"));

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
    if (props.env && ["jupyter_widgets", "jupyter_extension", "streamlit", "gradio", "marimo", "anywidget", "web_server"].indexOf(props.env) !== -1 && props.useSaveTool) {
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
                <HostShadowSlot>
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
                    />
                </HostShadowSlot> :
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
                        <HostShadowSlot>
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
                            />
                        </HostShadowSlot> :
                        <HostShadowSlot>
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
                        </HostShadowSlot>
                    )
                }
                {
                    expand && commonStore.isStreamlitComponent && (
                        <div style={{minWidth: "96%"}}>
                            <HostShadowSlot>
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
                            </HostShadowSlot>
                        </div>
                    )
                }
                { commonStore.isStreamlitComponent && expand && ( <ChevronLeftIcon className='h-6 w-6 cursor-pointer border border-black-600 rounded-full'onClick={() => setExpand(false)}></ChevronLeftIcon> )}
                { commonStore.isStreamlitComponent && !expand && ( <ChevronRightIcon className='h-6 w-6 cursor-pointer border border-black-600 rounded-full'onClick={() => setExpand(true)}></ChevronRightIcon> )}
            </div>
        </React.StrictMode>
    )
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
                            <HostShadowSlot>
                                <GraphicRenderer
                                    {...globalProps}
                                    computation={computationCallback!}
                                    chart={[chart]}
                                />
                            </HostShadowSlot> :
                            <HostShadowSlot>
                                <GraphicRenderer
                                    {...globalProps}
                                    data={props.dataSource!}
                                    chart={[chart]}
                                />
                            </HostShadowSlot>
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
                <HostShadowSlot>
                    <TableWalker
                        {...globalProps}
                        computation={computationCallback!}
                    />
                </HostShadowSlot> :
                <HostShadowSlot>
                    <TableWalker
                        {...globalProps}
                        data={props.dataSource}
                    />
                </HostShadowSlot>
            }
        </React.StrictMode>
    )
}

export { GWalkerComponent };
