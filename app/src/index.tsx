import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactDOM from 'react-dom';
import { observer } from "mobx-react-lite";
import { GraphicWalker } from '@kanaries/graphic-walker'
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'
import type { IStoInfo } from '@kanaries/graphic-walker/dist/utils/save';
import { IDataSetInfo, IMutField, IRow } from '@kanaries/graphic-walker/dist/interfaces';
import { AuthWrapper } from "@kanaries/auth-wrapper"
import {
  CodeBracketSquareIcon,
  UserIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

import Options from './components/options';
import LoadingIcon from './components/loadingIcon';
import { IAppProps } from './interfaces';
import NotificationWrapper, { useNotification } from "./notify";

import { loadDataSource, postDataService, finishDataService } from './dataSource';

import initCommunication from "./utils/communication";
import communicationStore from "./store/communication"
import { setConfig, checkUploadPrivacy } from './utils/userConfig';
import CodeExportModal from './components/codeExportModal';
import LoadDataModal from './components/loadDataModal';

import { ToolbarItemProps } from '@kanaries/graphic-walker/dist/components/toolbar';
// @ts-ignore
import style from './index.css?inline'

/** App does not consider props.storeRef */
const App: React.FC<IAppProps> = observer((propsIn) => {
  const storeRef = React.useRef<IGlobalStore|null>(null);
  const {dataSource, ...props} = propsIn;
  const { visSpec, dataSourceProps, rawFields, userConfig } = props;
  if (!props.storeRef?.current) {
    props.storeRef = storeRef;
  }
  const wrapRef = useRef<HTMLElement | null>(null);
  const [mounted, setMounted] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const { notify } = useNotification();

  useEffect(() => {
    if (userConfig) setConfig(userConfig);
  }, [userConfig]);

  const setData = useCallback(async (p: {
    data?: IRow[];
    rawFields?: IMutField[];
    visSpec?: string
  }) => {
    const { data, rawFields, visSpec } = p;
      if (visSpec) {
        const specList = JSON.parse(visSpec);
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
      } else {
        storeRef?.current?.commonStore?.updateTempSTDDS({
          name: 'Dataset',
          rawFields: rawFields,
          dataSource: data,
        } as IDataSetInfo);
        storeRef?.current?.commonStore?.commitTempDS();
      }
  }, [storeRef])

  useEffect(() => {
    setData({ data: dataSource, rawFields, visSpec });
  }, [dataSource, rawFields, visSpec]);

  const updateDataSource = useCallback(async () => {

    // TODO: don't always update visSpec when appending data
    await loadDataSource(dataSourceProps).then(ds => {
      const data = ds;
      setData({ data, rawFields, visSpec });
    }).catch(e => {
      console.error('Load DataSource Error', e);
    });
  }, [dataSource, dataSourceProps, rawFields, visSpec, setData]);

  useEffect(() => {
    if (storeRef.current) {
      // TODO: DataSet and DataSource ID
      try {
        updateDataSource();
      } catch (e) {
        console.error('failed to load spec: ', e);
      }
    }
  }, [updateDataSource]);

  const exportTool: ToolbarItemProps = {
    key: "export_code",
    label: "export_code",
    icon: (iconProps?: any) => <CodeBracketSquareIcon {...iconProps} />,
    onClick: () => { setExportOpen(true); }
  }
  const loginTool = {
    key: 'login',
    label: 'login',
    icon: (iconProps?: any) => (
      <UserIcon {...iconProps} ref={e => {
        setMounted(true);
        wrapRef.current = e?.parentElement as HTMLElement;
      }} />
    ),
    onClick: () => {}
  }
  const saveTool = {
    key: "save",
    label: "save",
    icon: (iconProps?: any) => {
        return saving ? <LoadingIcon width={36} height={36} /> : <DocumentTextIcon {...iconProps} />
    },
    onClick: () => {
        if (props.specType !== "json_file") {
            notify({
                type: "warning",
                title: "Tips",
                message: "spec params is not 'json_file', save is not supported.",
            }, 4_000)
            return
        }
        setSaving(true);
        communicationStore.comm?.sendMsg("update_vis_spec", {
            "content": JSON.stringify(storeRef.current?.vizStore?.exportViewSpec()),
        }).then(() => {
            setTimeout(() => {
                notify({
                    type: "success",
                    title: "Tips",
                    message: "save success.",
                }, 4_000);
                setSaving(false);
            }, 500);
        })
    }
  }

  const tools = [exportTool, saveTool];
  if (checkUploadPrivacy()) {
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
            mounted && checkUploadPrivacy() && <AuthWrapper id={props["id"]} wrapRef={wrapRef} />
        }
        <CodeExportModal open={exportOpen} setOpen={setExportOpen} globalStore={storeRef} sourceCode={props["sourceInvokeCode"] || ""} />
        <GraphicWalker {...props} toolbar={toolbarConfig} />
        <LoadDataModal />
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
}

const defaultInit = async(props: IAppProps) => {}


function GWalker(props: IAppProps, id: string) {
    const preRender = props.env === "jupyter" ? initOnJupyter : defaultInit;

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
