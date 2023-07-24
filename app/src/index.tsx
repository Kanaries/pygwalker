import React, { useEffect, useRef, useState } from 'react';
import ReactDOM from 'react-dom';
import { observer } from "mobx-react-lite";
import { GraphicWalker } from '@kanaries/graphic-walker'
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'
import type { IStoInfo } from '@kanaries/graphic-walker/dist/utils/save';
import { IDataSetInfo, IMutField, IRow, IGWHandler } from '@kanaries/graphic-walker/dist/interfaces';
import { AuthWrapper } from "@kanaries/auth-wrapper"

import Options from './components/options';
import { IAppProps } from './interfaces';
import NotificationWrapper from "./notify";

import { loadDataSource, postDataService, finishDataService } from './dataSource';

import commonStore from "./store/common";
import initCommunication from "./utils/communication";
import { decodeSpec } from "./utils/graphicWalkerParser"
import communicationStore from "./store/communication"
import { setConfig, checkUploadPrivacy } from './utils/userConfig';
import CodeExportModal from './components/codeExportModal';
import InitModal from './components/initModal';
import { getSaveTool, hidePreview } from './tools/saveTool';
import { getExportTool } from './tools/exportTool';
import { getLoginTool } from './tools/loginTool';
import { domToPng } from "./utils/screenshot"

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
            const singleChart = await domToPng(chart.data.container()!);
            await communicationStore.comm?.sendMsg("save_chart", {...chart.data, singleChart});
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
    const wrapRef = useRef<HTMLElement | null>(null);
    const [mounted, setMounted] = useState(false);
    const [exportOpen, setExportOpen] = useState(false);
    const specList = props.visSpec ? decodeSpec(props.visSpec) : [];

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
    }, []);

    const exportTool = getExportTool(setExportOpen);
    const saveTool = getSaveTool(props, gwRef, storeRef);
    const loginTool = getLoginTool(setMounted, wrapRef);

    const tools = [exportTool];
    if (props.env === "jupyter_widgets") {
        tools.push(saveTool);
    }
    if (checkUploadPrivacy() && commonStore.showCloudTool) {
        tools.push(loginTool);
    }

    const toolbarConfig = {
        exclude: ["export_code"],
        extra: tools
    }
  
  return (
    <React.StrictMode>
        <style>{style}</style>
        {
            mounted && checkUploadPrivacy() && commonStore.showCloudTool && <AuthWrapper id={props["id"]} wrapRef={wrapRef} />
        }
        <CodeExportModal open={exportOpen} setOpen={setExportOpen} globalStore={storeRef} sourceCode={props["sourceInvokeCode"] || ""} />
        <GraphicWalker {...props} storeRef={storeRef} ref={gwRef} toolbar={toolbarConfig} />
        <InitModal />
        <Options {...props} toolbar={toolbarConfig} />
    </React.StrictMode>
  );
})

const initOnJupyter = async(props: IAppProps) => {
    const comm = initCommunication(props.id);
    comm.registerEndpoint("postData", postDataService);
    comm.registerEndpoint("finishData", finishDataService);
    communicationStore.setComm(comm);
    const visSpecResp = await comm.sendMsg("get_latest_vis_spec", {});
    props.visSpec = visSpecResp["data"]["visSpec"];
    if (props.needLoadDatas) {
        comm.sendMsgAsync("request_data", {}, null);
    }
    hidePreview(props.id);
}

const defaultInit = async(props: IAppProps) => {}


function GWalker(props: IAppProps, id: string) {
    const preRender = props.env === "jupyter_widgets" ? initOnJupyter : defaultInit;

    preRender(props).then(() => {
        ReactDOM.render(
            <NotificationWrapper>
                <App {...props}></App>
            </NotificationWrapper>,
            document.getElementById(id)
        );
    })
}

export default { GWalker }
