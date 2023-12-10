import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { observer } from "mobx-react-lite";
import { GraphicWalker, PureRenderer } from '@kanaries/graphic-walker'
import type { VizSpecStore } from '@kanaries/graphic-walker/dist/store/visualSpecStore'
import { IRow, IGWHandler, IViewField } from '@kanaries/graphic-walker/dist/interfaces';

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
import initDslParser from "@kanaries-temp/gw-dsl-parser";

// @ts-ignore
import style from './index.css?inline'


const initChart = async (gwRef: React.MutableRefObject<IGWHandler | null>, total: number, props: IAppProps) => {
    if (props.needInitChart && props.env === "jupyter_widgets" && total !== 0) {
        commonStore.initModalOpen = true;
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

const App: React.FC<IAppProps> = observer((props) => {
    const storeRef = React.useRef<VizSpecStore|null>(null);
    const gwRef = React.useRef<IGWHandler|null>(null);
    const { dataSourceProps, userConfig } = props;
    const [exportOpen, setExportOpen] = useState(false);
    const [uploadChartModalOpen, setUploadChartModalOpen] = useState(false);
    const visSpec = props.visSpec;
    const [dataSource, setDataSource] = useState<IRow[]>(props.dataSource);
    commonStore.setVersion(props.version!);

    const updateDataSource = () => {
        loadDataSource(dataSourceProps).then((data) => {
            setDataSource(data);
            initChart(gwRef, visSpec.length, props);
        }).catch(e => {
            console.error('Load DataSource Error', e);
        });
    }

    useEffect(() => {
        commonStore.setShowCloudTool(props.showCloudTool);
        if (visSpec.length !== 0) {
            setTimeout(() => { storeRef.current?.importCode(visSpec); }, 0);
        }
        if (props.needLoadDatas) {
            updateDataSource()
        } else {
            setTimeout(() => { initChart(gwRef, visSpec.length, props) }, 0);
        }
        updateDataSource();
        if (userConfig) setConfig(userConfig);
        // temporary notifcation
        if (props.useKernelCalc) {
            commonStore.setNotification({
                type: "info",
                title: "Tips",
                message: "in `useKernelCalc` mode, If your dataset too big, not suitable for some non-aggregated charts, such as scatter.",
            }, 6_000);   
        }
    }, []);

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
  
    return (
        <React.StrictMode>
            <style>{style}</style>
            <Notification />
            <UploadSpecModal />
            <UploadChartModal gwRef={gwRef} storeRef={storeRef} open={uploadChartModalOpen} setOpen={setUploadChartModalOpen} />
            <CodeExportModal open={exportOpen} setOpen={setExportOpen} globalStore={storeRef} sourceCode={props["sourceInvokeCode"] || ""} />
            <GraphicWalker
                {...props.extraConfig}
                dark={props.dark}
                themeKey={props.themeKey}
                hideDataSourceConfig={props.hideDataSourceConfig}
                fieldkeyGuard={props.fieldkeyGuard}
                rawFields={props.rawFields}
                dataSource={props.useKernelCalc ? undefined : dataSource}
                storeRef={storeRef}
                ref={gwRef}
                toolbar={toolbarConfig}
                computation={computationCallback}
                enhanceAPI={enhanceAPI}
            />
            <InitModal />
            <Options {...props} />
        </React.StrictMode>
    );
})

const PureRednererApp: React.FC<IAppProps> = observer((props) => {
    const computationCallback = getComputationCallback(props);
    const spec = props.visSpec[0];

    return (
        <React.StrictMode>
            <style>{style}</style>
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
        props.visSpec = visSpecResp["data"]["visSpec"];
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
    if (props.gwMode === "explore" && props.needLoadLastSpec) {
        const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
        props.visSpec = visSpecResp["data"]["visSpec"];
    }
    await initDslParser();
}

const defaultInit = async(props: IAppProps) => {}


function GWalker(props: IAppProps, id: string) {
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
            props.gwMode === "explore" ? <App {...props} /> : <PureRednererApp {...props} />,
            document.getElementById(id)
        );
    })
}

function PreviewApp(props: IPreviewProps, id: string) {
    ReactDOM.render(
        <Preview {...props} />,
        document.getElementById(id)
    );
}

function ChartPreviewApp(props: IChartPreviewProps, id: string) {
    ReactDOM.render(
        <ChartPreview {...props} />,
        document.getElementById(id)
    );
}

export default { GWalker, PreviewApp, ChartPreviewApp }
