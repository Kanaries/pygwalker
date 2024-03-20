import React, { useContext, useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { observer } from "mobx-react-lite";
import { GraphicWalker, PureRenderer, GraphicRenderer, TableWalker } from '@kanaries/graphic-walker'
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore'
import type { IRow, IGWHandler, IViewField, ISegmentKey, IDarkMode } from '@kanaries/graphic-walker/interfaces';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import Options from './components/options';
import { IAppProps } from './interfaces';

import { loadDataSource, postDataService, finishDataService, getDatasFromKernelBySql, getDatasFromKernelByPayload } from './dataSource';

import commonStore from "./store/common";
import { initJupyterCommunication, initHttpCommunication } from "./utils/communication";
import communicationStore from "./store/communication"
import { setConfig, checkUploadPrivacy } from './utils/userConfig';
import CodeExportModal from './components/codeExportModal';
import type { IPreviewProps, IChartPreviewProps } from './components/preview';
import { Preview, ChartPreview } from './components/preview';
import UploadSpecModal from "./components/uploadSpecModal"
import UploadChartModal from './components/uploadChartModal';
import InitModal from './components/initModal';
import { getSaveTool, hidePreview } from './tools/saveTool';
import { getExportTool } from './tools/exportTool';
import { getExportDataframeTool } from './tools/exportDataframe';
import { getUploadChartTool } from './tools/uploadChartTool';
import { formatExportedChartDatas } from "./utils/save";
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
import { SunIcon, MoonIcon, DesktopIcon } from "@radix-ui/react-icons"

// @ts-ignore
import style from './index.css?inline'
import { currentMediaTheme } from './utils/theme';
import { AppContext, darkModeContext } from './store/context';
import FormatSpec from './utils/formatSpec';


const initChart = async (gwRef: React.MutableRefObject<IGWHandler | null>, total: number, props: IAppProps) => {
    if (props.needInitChart && props.env === "jupyter_widgets" && total !== 0) {
        commonStore.setInitModalOpen(true);
        commonStore.setInitModalInfo({
            title: "Recover Charts",
            curIndex: 0,
            total: total,
        });
        for await (const chart of gwRef.current?.exportChartList("data-url")!) {
            await communicationStore.comm?.sendMsg("save_chart", await formatExportedChartDatas(chart.data));
            commonStore.setInitModalInfo({
                title: "Recover Charts",
                curIndex: chart.index + 1,
                total: chart.total,
            });
            hidePreview(props.id);
        }
    }
    commonStore.setInitModalOpen(false);
}

const getComputationCallback = (props: IAppProps) => {
    if (props.useKernelCalc && props.parseDslType === "client") {
        return getDatasFromKernelBySql(props.fieldMetas);
    }
    if (props.useKernelCalc && props.parseDslType === "server") {
        return getDatasFromKernelByPayload;
    }
}

const MainApp = observer((props: {children: React.ReactNode, darkMode: "dark" | "light" | "media", hideToolBar?: boolean}) => {
    const [portal, setPortal] = useState<HTMLDivElement | null>(null);
    const [selectedDarkMode, setSelectedDarkMode] = useState(props.darkMode);
    const [darkMode, setDarkMode] = useState(currentMediaTheme(props.darkMode));

    useEffect(() => {
        if (selectedDarkMode === "media") {
            setDarkMode(currentMediaTheme(selectedDarkMode));
            const media = window.matchMedia('(prefers-color-scheme: dark)');
            const listener = (e: MediaQueryListEvent) => {
                setDarkMode(e.matches ? "dark" : "light");
            }
            media.addEventListener("change", listener);
            return () => media.removeEventListener("change", listener);
        } else {
            setDarkMode(selectedDarkMode);
        }
    }, [selectedDarkMode])

    return (
        <AppContext
            portalContainerContext={portal}
            darkModeContext={darkMode}
        >
            <div className={`${darkMode === "dark" ? "dark": ""} bg-background text-foreground p-2`}>
                <style>{style}</style>
                <div className='overflow-y-auto'>
                    { props.children }
                </div>
                {!props.hideToolBar && (
                    <div className="flex w-full mt-1 p-1 overflow-hidden border-t border-border">
                        <ToggleGroup
                            type="single"
                            value={selectedDarkMode}
                            onValueChange={(value) => {setSelectedDarkMode(value as IDarkMode)}}
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
                <InitModal />
                <div ref={setPortal}></div>
            </div>
        </AppContext>
    )
})

const ExploreApp: React.FC<IAppProps & {initChartFlag: boolean}> = (props) => {
    const storeRef = React.useRef<VizSpecStore|null>(null);
    const gwRef = React.useRef<IGWHandler|null>(null);
    const { userConfig } = props;
    const [exportOpen, setExportOpen] = useState(false);
    const [uploadChartModalOpen, setUploadChartModalOpen] = useState(false);
    const [mode, setMode] = useState<string>("walker");
    const [visSpec, setVisSpec] = useState(props.visSpec);
    const [hideModeOption, _] = useState(true);
    commonStore.setVersion(props.version!);

    useEffect(() => {
        commonStore.setShowCloudTool(props.showCloudTool);
        if (userConfig) setConfig(userConfig);
    }, []);

    useEffect(() => {
        if (props.initChartFlag) {
            setTimeout(() => { initChart(gwRef, visSpec.length, props) }, 0);
        }
    }, [props.initChartFlag]);

    useEffect(() => {
        setTimeout(() => {
            storeRef.current?.setSegmentKey(props.defaultTab as ISegmentKey);
        }, 0);
    }, [mode]);

    const exportTool = getExportTool(setExportOpen);

    const tools = [exportTool];
    if ((props.env === "jupyter_widgets" || props.env === "streamlit" || props.env === "gradio") && props.useSaveTool) {
        const saveTool = getSaveTool(props, gwRef, storeRef);
        tools.push(saveTool);
    }
    if (props.isExportDataFrame) {
        const exportDataFrameTool = getExportDataframeTool(props, storeRef);
        tools.push(exportDataFrameTool);
    }
    if (checkUploadPrivacy() && commonStore.showCloudTool) {
        const uploadTool = getUploadChartTool(setUploadChartModalOpen);
        tools.push(uploadTool);
    }

    const toolbarConfig = {
        exclude: ["export_code"],
        extra: tools
    }

    const computationCallback = getComputationCallback(props);
    let enhanceAPI;
    if (props.showCloudTool) {
        enhanceAPI = {
            features: {
                "askviz": async (metas: IViewField[], query: string) => {
                    const resp = await communicationStore.comm?.sendMsg("get_spec_by_text", { metas, query });
                    return resp?.data.data;
                }
            }
        }
    }

    const modeChange = (value: string) => {
        if (mode === "walker") {
            setVisSpec(storeRef.current?.exportCode());
        }
        setMode(value);
    }
  
    return (
        <React.StrictMode>
            <Notification />
            <UploadSpecModal />
            <UploadChartModal gwRef={gwRef} storeRef={storeRef} open={uploadChartModalOpen} setOpen={setUploadChartModalOpen} dark={useContext(darkModeContext)} />
            <CodeExportModal open={exportOpen} setOpen={setExportOpen} globalStore={storeRef} sourceCode={props["sourceInvokeCode"] || ""} />
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
                    dark={useContext(darkModeContext)}
                    themeKey={props.themeKey}
                    fieldkeyGuard={props.fieldkeyGuard}
                    rawFields={props.rawFields}
                    dataSource={props.useKernelCalc ? undefined : props.dataSource}
                    storeRef={storeRef}
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

    return (
        <React.StrictMode>
            <PureRenderer
                {...props.extraConfig}
                name={spec.name}
                visualConfig={spec.config}
                visualLayout={spec.layout}
                visualState={spec.encodings}
                type='remote'
                computation={computationCallback!}
            />
        </React.StrictMode>
    )
});

const initOnJupyter = async(props: IAppProps) => {
    const comm = initJupyterCommunication(props.id);
    comm.registerEndpoint("postData", postDataService);
    comm.registerEndpoint("finishData", finishDataService);
    communicationStore.setComm(comm);
    if (props.needLoadLastSpec) {
        const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
        props.visSpec = FormatSpec(visSpecResp["data"]["visSpec"], props.rawFields);
    }
    if (props.needLoadDatas) {
        comm.sendMsgAsync("request_data", {}, null);
    }
    await initDslParser();
    hidePreview(props.id);
}

const initOnHttpCommunication = async(props: IAppProps) => {
    const comm = initHttpCommunication(props.id, props.communicationUrl);
    communicationStore.setComm(comm);
    if ((props.gwMode === "explore" || props.gwMode === "filter_renderer") && props.needLoadLastSpec) {
        const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
        props.visSpec = visSpecResp["data"]["visSpec"];
    }
    await initDslParser();
}

const defaultInit = async(props: IAppProps) => {}

function GWalkerComponent(props: IAppProps) {
    const [initChartFlag, setInitChartFlag] = useState(false);

    useEffect(() => {
        if (props.needLoadDatas) {
            loadDataSource(props.dataSourceProps).then((data) => {
                props.dataSource = data;
                setInitChartFlag(true);
                commonStore.setInitModalOpen(false);
            })
        } else {
            setInitChartFlag(true);
        }
    }, []);

    switch(props.gwMode) {
        case "explore":
            return <ExploreApp {...props} initChartFlag={initChartFlag} />;
        case "renderer":
            return <PureRednererApp {...props} />;
        case "filter_renderer":
            return <GraphicRendererApp {...props} />;
        case "table":
            return <TableWalkerApp {...props} />;
        default:
            return<ExploreApp {...props} initChartFlag={initChartFlag} />
    }
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
        default:
            preRender = defaultInit;
    }

    preRender(props).then(() => {
        ReactDOM.render(
            <MainApp darkMode={props.dark}>
                <GWalkerComponent {...props} />
            </MainApp>,
            document.getElementById(id)
        );
    })
}

function PreviewApp(props: IPreviewProps, id: string) {
    props.charts = FormatSpec(props.charts.map(chart => chart.visSpec), [])
                    .map((visSpec, index) => { return {...props.charts[index], visSpec} });
    ReactDOM.render(
        <MainApp darkMode={props.dark} hideToolBar>
            <Preview {...props} />
        </MainApp>,
        document.getElementById(id)
    );
}

function ChartPreviewApp(props: IChartPreviewProps, id: string) {
    props.visSpec = FormatSpec(props.visSpec, []);
    ReactDOM.render(
        <MainApp darkMode={props.dark} hideToolBar>
            <ChartPreview {...props} />
        </MainApp>,
        document.getElementById(id)
    );
}

function GraphicRendererApp(props: IAppProps) {
    const computationCallback = getComputationCallback(props);
    const globalProps = {
        rawFields: props.rawFields,
        containerStyle: { height: "700px", width: "60%" },
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
                                dataSource={props.dataSource!}
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
                    dataSource={props.dataSource}
                />
            }
        </React.StrictMode>
    )
}

export default { GWalker, PreviewApp, ChartPreviewApp }
