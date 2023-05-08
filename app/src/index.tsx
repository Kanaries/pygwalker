import React, { useCallback, useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { GraphicWalker } from '@kanaries/graphic-walker'
//import type { IGWProps } from '../../graphic-walker/packages/graphic-walker/dist/App'
//import type { IGlobalStore } from '../../graphic-walker/packages/graphic-walker/dist/store'
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'
// import type { IGWProps } from 'gwalker/App'

import Options from './components/options';
import { IAppProps } from './interfaces';
import type { IStoInfo } from '@kanaries/graphic-walker/dist/utils/save';
import { loadDataSource } from './dataSource';
import { IDataSetInfo, IGWEvent, IMutField, IRow } from '@kanaries/graphic-walker/dist/interfaces';
import { getConfig, setConfig } from './utils/userConfig';
import { Tunnel } from './tunnel';

const App: React.FC<IAppProps> = (propsIn) => {
  const storeRef = React.useRef<IGlobalStore|null>(null);
  const {dataSource, ...props} = propsIn;
  const { visSpec, dataSourceProps, rawFields, userConfig } = props;
  const { tunnelId, dataSourceId } = dataSourceProps;

  if (!props.storeRef?.current) {
    props.storeRef = storeRef;
  }
  const [tunnel, setTunnel] = useState<Tunnel|null>(null);
  const vizStore = props.storeRef.current?.vizStore;

  useEffect(() => {
    if (userConfig) setConfig(userConfig);
  }, [userConfig]);

  useEffect(() => {
    if (tunnelId) {
      if (process.env.NODE_ENV === 'develop') console.log("tunnelId = ", tunnelId);
      const newTunnel = new Tunnel(tunnelId, window);
      setTunnel(newTunnel);
      newTunnel.onMessage((msg, ...props) => {
        if (process.env.NODE_ENV === 'develop') {
          console.log("tunnel msg from kernel = ", msg, props);
        }
        /** TODO: Kernel Message Handler */
      })
    }
    else {
      setTunnel(null);
    }
    return () => {
      tunnel?.close();
    }
  }, [tunnelId])

  const onEvent = useCallback(async (event: IGWEvent) => {
    const { privacy } = getConfig();
    try{
    if (event.type === 'specChange') {
      const { visSpec, prev } = event.detail;
      const specList = visSpec;
      const canvas = ''; // await rendererRef.current?.getCanvasData();
      if (process.env.NODE_ENV === 'develop') {
        console.log(event.detail);
        // console.log('canvas = ', canvas);
      }
      if (privacy !== 'offline' && privacy !== 'get-only') {
        tunnel?.send({
          action: 'updateSpec',
          data: {
            dataSourceId,
            specList,
            visIndex: vizStore?.visIndex,
            canvas,
          },
        });
      }
    }
    } catch(e) { console.error();}
  }, [tunnel, dataSourceId]);

  const setData = useCallback(async (p: {
    data?: IRow[];
    rawFields?: IMutField[];
    visSpec?: string
  }) => {
    const { data, rawFields, visSpec } = p;
    const globalStore = props.storeRef!.current;
    if (!globalStore) return;
    const { commonStore, vizStore } = globalStore;
    if (visSpec) {
      const specList = JSON.parse(visSpec);
      vizStore.importStoInfo({
        dataSources: [{
          id: dataSourceId ?? 'dataSource-0',
          data: data,
        }],
        datasets: [{
          id: 'dataset-0',
          name: 'DataSet', rawFields: rawFields, dsId: dataSourceId,
        }],
        specList,
      } as IStoInfo);
    } else {
      commonStore.updateTempSTDDS({
        name: 'Dataset',
        rawFields: rawFields,
        dataSource: data,
      } as IDataSetInfo);
      commonStore?.commitTempDS();
    }
  }, [props.storeRef, dataSourceId])

  const updateDataSource = async () => {
    // TODO: don't always update visSpec when appending data
    await loadDataSource(dataSourceProps).then(ds => {
      const data = [...(dataSource || []), ...ds];
      setData({ data, rawFields, visSpec });
    }).catch(e => {
      console.error('Load DataSource Error', e);
    });
  };

  useEffect(() => {
    // TODO: DataSet and DataSource ID
    // updateDataSource();
    const listener = (ev: MessageEvent & any) => {
      if (ev.data.action === 'startData'
      && ev.data.tunnelId === tunnelId
      && ev.data.dataSourceId === dataSourceId) {
        updateDataSource();
      }
    };
    window.addEventListener('message', listener);
    return () => {
      window.removeEventListener('message', listener);
    }
  }, []);

  useEffect(() => {
    setData({ data: dataSource, rawFields, visSpec });
  }, [dataSource, rawFields, visSpec, setData]);

  return (
    <React.StrictMode>
      <GraphicWalker {...props} onEvent={onEvent}/>
      <Options {...props} />
    </React.StrictMode>
  );
}

function GWalker(props: IAppProps, id: string) {
    // GWalkerMap[id] = c;
    ReactDOM.render(<App {...props}></App>, document.getElementById(id)
  );
}

// export {IGWProps}
export default { GWalker }