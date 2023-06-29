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
  UserIcon
} from '@heroicons/react/24/outline';

import Options from './components/options';
import { IAppProps } from './interfaces';

import { loadDataSource } from './dataSource';

import { setConfig, checkUploadPrivacy } from './utils/userConfig';
import CodeExportModal from './components/codeExportModal';

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

  const toolbarConfig = {
    exclude: ["export_code"],
    extra: checkUploadPrivacy() ? [exportTool, loginTool] : [exportTool]
  }
  
  return (
    <React.StrictMode>
      <style>{style}</style>
      {
        mounted && checkUploadPrivacy() && <AuthWrapper id={props["id"]} wrapRef={wrapRef} />
      }
      <CodeExportModal open={exportOpen} setOpen={setExportOpen} globalStore={storeRef} sourceCode={props["sourceInvokeCode"] || ""} />
      <GraphicWalker {...props} toolbar={toolbarConfig} />
      <Options {...props} toolbar={toolbarConfig} />
    </React.StrictMode>
  );
})

function GWalker(props: IAppProps, id: string) {
    ReactDOM.render(<App {...props}></App>, document.getElementById(id)
  );
}

export default { GWalker }
