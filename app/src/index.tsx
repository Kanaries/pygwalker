import React from 'react';
import ReactDOM from 'react-dom';
import { GraphicWalker } from '@kanaries/graphic-walker'
// import type { IGWProps } from '@kanaries/graphic-walker/dist/App'
// import type { IGWProps } from 'gwalker/App'

function GWalker(props: any, id: string) {
    const c = 
    (<React.StrictMode>
        <GraphicWalker {...props} />
    </React.StrictMode>);
    // GWalkerMap[id] = c;
    ReactDOM.render(c, document.getElementById(id)
  );
}

// export {IGWProps}
export default { GWalker }