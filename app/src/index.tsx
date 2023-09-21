import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { observer } from "mobx-react-lite";
import { GraphicWalker } from '@kanaries/graphic-walker'
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'
import type { IStoInfo } from '@kanaries/graphic-walker/dist/utils/save';
import { IDataSetInfo, IMutField, IRow, IGWHandler } from '@kanaries/graphic-walker/dist/interfaces';

import Options from './components/options';
import { IAppProps } from './interfaces';

import { loadDataSource, postDataService, finishDataService, getDatasFromKernelBySql, getDatasFromKernelByPayload } from './dataSource';

import commonStore from "./store/common";
import { initJupyterCommunication, initStreamlitCommunication } from "./utils/communication";
import communicationStore from "./store/communication"
import { setConfig, checkUploadPrivacy } from './utils/userConfig';
import CodeExportModal from './components/codeExportModal';
import ShareModal from './components/shareModal';
import InitModal from './components/initModal';
import { getSaveTool, hidePreview } from './tools/saveTool';
import { getExportTool } from './tools/exportTool';
import { getShareTool } from './tools/shareTool';
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

const App: React.FC<IAppProps> = observer((propsIn) => {
    const storeRef = React.useRef<IGlobalStore|null>(null);
    const gwRef = React.useRef<IGWHandler|null>(null);
    const {dataSource, ...props} = propsIn;
    const { dataSourceProps, rawFields, userConfig } = props;
    const [exportOpen, setExportOpen] = useState(false);
    const [shareModalOpen, setShareModalOpen] = useState(false);
    const specList = props.visSpec ? JSON.parse(props.visSpec) : [];
    commonStore.setVersion(props.version!);

    const setData = (data?: IRow[], rawFields?: IMutField[]) => {
        if (specList.length !== 0) {
            setTimeout(() => {
                storeRef?.current?.vizStore?.importStoInfo({
                    dataSources: [{
                        id: 'dataSource-0',
                        data: data,
                    }],
                    datasets: [{
                        id: 'dataset-0',
                        name: 'DataSet', rawFields: rawFields, dsId: 'dataSource-0',
                    }],
                    specList,
                } as IStoInfo);
            }, 0);
        } else {
            storeRef?.current?.commonStore?.updateTempSTDDS({
                name: 'Dataset',
                rawFields: rawFields,
                dataSource: data,
            } as IDataSetInfo);
            storeRef?.current?.commonStore?.commitTempDS();
        }
        if (!props.needLoadDatas) {
            setTimeout(() => { initChart(gwRef, specList.length, props) }, 0);
        }
    }

    const updateDataSource = () => {
        loadDataSource(dataSourceProps).then((data) => {
            setData(data, rawFields);
            initChart(gwRef, specList.length, props);
        }).catch(e => {
            console.error('Load DataSource Error', e);
        });
    }

    useEffect(() => {
        setData(dataSource, rawFields);
        commonStore.setShowCloudTool(props.showCloudTool);
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
    const saveTool = getSaveTool(props, gwRef, storeRef);
    const uploadTool = getShareTool(setShareModalOpen);

    const tools = [exportTool];
    if ((props.env === "jupyter_widgets" || props.env === "streamlit") && props.useSaveTool) {
        tools.push(saveTool);
    }
    if (checkUploadPrivacy() && commonStore.showCloudTool) {
        tools.push(uploadTool);
    }

    const toolbarConfig = {
        exclude: ["export_code"],
        extra: tools
    }

    let computationCallback;
    if (props.useKernelCalc && props.parseDslType === "client") {
        computationCallback = getDatasFromKernelBySql;
    }
    if (props.useKernelCalc && props.parseDslType === "server") {
        computationCallback = getDatasFromKernelByPayload;
    }
  
    return (
        <React.StrictMode>
            <style>{style}</style>
            <Notification />
            <CodeExportModal open={exportOpen} setOpen={setExportOpen} globalStore={storeRef} sourceCode={props["sourceInvokeCode"] || ""} />
            <ShareModal gwRef={gwRef} storeRef={storeRef} open={shareModalOpen} setOpen={setShareModalOpen} />
            <GraphicWalker {...props} storeRef={storeRef} ref={gwRef} toolbar={toolbarConfig} computation={computationCallback} />
            <InitModal />
            <Options {...props} toolbar={toolbarConfig} />
        </React.StrictMode>
    );
})

const initOnJupyter = async(props: IAppProps) => {
    const comm = initJupyterCommunication(props.id);
    comm.registerEndpoint("postData", postDataService);
    comm.registerEndpoint("finishData", finishDataService);
    communicationStore.setComm(comm);
    const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
    props.visSpec = visSpecResp["data"]["visSpec"];
    if (props.needLoadDatas) {
        comm.sendMsgAsync("request_data", {}, null);
    }
    if (props.useKernelCalc) {
        await initDslParser();
    }
    hidePreview(props.id);
}

const initOnStreamlit = async(props: IAppProps) => {
    const comm = initStreamlitCommunication(props.id);
    communicationStore.setComm(comm);
    const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
    props.visSpec = visSpecResp["data"]["visSpec"];
    if (props.useKernelCalc) {
        await initDslParser();
    }
}

const defaultInit = async(props: IAppProps) => {}


function GWalker(props: IAppProps, id: string) {
    let preRender = defaultInit;
    switch(props.env) {
        case "jupyter_widgets":
            preRender = initOnJupyter;
            break;
        case "streamlit":
            preRender = initOnStreamlit;
            break;
        default:
            preRender = defaultInit;
    }

    preRender(props).then(() => {
        ReactDOM.render(
            <App {...props}></App>,
            document.getElementById(id)
        );
    })
}

export default { GWalker }
