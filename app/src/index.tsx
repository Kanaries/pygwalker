import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactDOM from 'react-dom';
import { observer } from "mobx-react-lite";
import { GraphicWalker } from '@kanaries/graphic-walker'
//import type { IGWProps } from '../../graphic-walker/packages/graphic-walker/dist/App'
//import type { IGlobalStore } from '../../graphic-walker/packages/graphic-walker/dist/store'
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'
// import type { IGWProps } from 'gwalker/App'

import style from "./index.css";
import Options from './components/options';
import { IAppProps } from './interfaces';
import type { IStoInfo } from '@kanaries/graphic-walker/dist/utils/save';
import { AuthWrapper } from "@kanaries/auth-wrapper"
import { loadDataSource } from './dataSource';
import { IDataSetInfo, IMutField, IRow } from '@kanaries/graphic-walker/dist/interfaces';
import { setConfig, checkUploadPrivacy } from './utils/userConfig';
import CodeExportModal from './components/codeExportModal';
import {
  CodeBracketSquareIcon,
  UserIcon
} from '@heroicons/react/24/outline';

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

  // let tunnel: Tunnel;
  useEffect(() => {
    if (userConfig) setConfig(userConfig);
  }, [userConfig]);

  // useEffect(() => {
  //   const tunnelId = dataSourceProps?.tunnelId;
  //   if (tunnelId) {
  //     console.log("tunnelId = ", tunnelId);
  //     tunnel = new Tunnel(tunnelId, window);
  //     tunnel.onMessage((msg) => {
  //       // TODO:
  //     })

  //     return () => {
  //       tunnel.close();
  //     }
  //   }
  // })

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
    // console.log('dataListener', ev);
    // if (ev.data.action !== 'dataReady') {
    //   return;
    // }
    // console.log("Data Ready!");
    // window.removeEventListener('message', dataListener);
    // console.log("props = ", props);

    // TODO: don't always update visSpec when appending data
    await loadDataSource(dataSourceProps).then(ds => {
      const data = [...(dataSource || []), ...ds];
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
        // console.log("message", dataListener);
        // window.addEventListener('message', dataListener);
      } catch (e) {
        console.error('failed to load spec: ', e);
      }
    }
  }, [updateDataSource]);

  const exportTool = { key: "export_code", label: "export_code", icon: CodeBracketSquareIcon, onClick: () => { setExportOpen(true); } }
  const loginTool = {
    key: 'login',
    label: 'login',
    icon: props => (
      <UserIcon {...props} ref={e => {
        setMounted(true);
        wrapRef.current = e?.parentElement as HTMLElement;
      }} />
    ),
    onClick: () => {}
  }

  const toolbarConfig = {
    exclude: ["export_code"],
    extra: checkUploadPrivacy() ? [exportTool, loginTool] : [exportTool]
  }
  props["toolbar"] = toolbarConfig
  
  return (
    <React.StrictMode>
      <style>{style}</style>
      {
        mounted && checkUploadPrivacy() && <AuthWrapper id={props["id"]} wrapRef={wrapRef} />
      }
      <CodeExportModal open={exportOpen} setOpen={setExportOpen} globalStore={storeRef} sourceCode={props["sourceInvokeCode"]} />
      <GraphicWalker {...props} />
      <Options {...props} />
    </React.StrictMode>
  );
})

function GWalker(props: IAppProps, id: string) {
    // GWalkerMap[id] = c;
    ReactDOM.render(<App {...props}></App>, document.getElementById(id)
  );
}

// export {IGWProps}
export default { GWalker }
