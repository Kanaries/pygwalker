import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import { GraphicWalker } from '@kanaries/graphic-walker'
//import type { IGWProps } from '../../graphic-walker/packages/graphic-walker/dist/App'
//import type { IGlobalStore } from '../../graphic-walker/packages/graphic-walker/dist/store'
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'
// import type { IGWProps } from 'gwalker/App'

import Options from './components/options';
import { IAppProps } from './interfaces';
import type { IStoInfo } from '@kanaries/graphic-walker/dist/utils/save';

/** App does not consider props.storeRef */
const App: React.FC<IAppProps> = (propsIn) => {
  const storeRef = React.useRef<IGlobalStore|null>(null);
  const props: IAppProps = {...propsIn};
  if (!props.storeRef?.current) {
    props.storeRef = storeRef;
  }

  useEffect(() => {
    if (props.visSpec && storeRef.current) {
      // TODO: DataSet and DataSource ID
      try {
        const specList = JSON.parse(props.visSpec);
        storeRef?.current?.vizStore?.importStoInfo({
          dataSources: [{
            id: 'dataSource-0',
            data: props.dataSource,
          }],
          datasets: [{
            id: 'dataset-0',
            name: 'DataSet', rawFields: props.rawFields, dsId: 'dataSource-0',
          }],
          specList: specList,
        } as IStoInfo);
      } catch (e) {
        console.error('failed to load spec: ', e);
      }
    }
  }, []);
  return (
    <React.StrictMode>
      <GraphicWalker {...props} />
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