import React from 'react';
import ReactDOM from 'react-dom';
import { GraphicWalker } from '@kanaries/graphic-walker'
import type { IGWProps } from '@kanaries/graphic-walker/dist/App'
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'
// import type { IGWProps } from 'gwalker/App'

import Options from './components/options';
import { IAppProps } from './interfaces';

const App: React.FC<IAppProps> = (props) => {
  const ref = React.useRef<IGlobalStore | null>(null);
  return (<React.StrictMode>
    <GraphicWalker {...props} storeRef={ref} />
    <div style={{
        position: 'absolute',
        top: '5%',
        marginTop: '50px',
        right: '20%',
        marginRight: '30px',
        backgroundColor: 'rgba(148,163,184,.1)',
        borderRadius: '9999px'
      }} >
      <Options {...props} storeRef={ref} />
    </div>
  </React.StrictMode>);
}

function GWalker(props: IAppProps, id: string) {
    // GWalkerMap[id] = c;
    ReactDOM.render(<App {...props}></App>, document.getElementById(id)
  );
}

// export {IGWProps}
export default { GWalker }