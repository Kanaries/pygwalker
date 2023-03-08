import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';
import { GraphicWalker } from '@kanaries/graphic-walker'
import type { IGWProps } from 'gwalker/App';

import type { View } from 'vega-typings'
import type { VizSpecStore } from 'gwalker/store/visualSpecStore';
import type { CommonStore } from 'gwalker/store/commonStore';
// import { dumpsGWPureSpec, parseGWContent, parseGWPureSpec, stringifyGWContent } from "@kanaries/graphic-walker/dist/utils/save"

const PyGWalkerApp: React.FC<IGWProps> = function(props: IGWProps) {
  const onVegaUpdate = (views: React.MutableRefObject<View[]>, store: {commonStore: CommonStore, vizStore: VizSpecStore}, ...args) => {
    const {commonStore, vizStore} = store;
    // (JSON.stringify(vizStore.visList[vizStore.visIndex].exportGW()));
  }
  return (
  <React.StrictMode>
    <GraphicWalker {...props} onVegaUpdate={onVegaUpdate} />
  </React.StrictMode>);
}


function GWalker(props: any, id: string) {
  const c = (<PyGWalkerApp {...props} />)
  ReactDOM.render(c, document.getElementById(id));
}

// export {IGWProps}
export default { GWalker }