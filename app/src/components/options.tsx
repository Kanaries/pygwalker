import React, { useEffect, useMemo, useState } from 'react'
import { IGWProps } from '@kanaries/graphic-walker/dist/App'
import { IAppProps } from '../interfaces';
const url = "https://5agko11g7e.execute-api.us-west-1.amazonaws.com/default/check_updates?pkg=pygwalker-app";

const appMeta = {};

const Options: React.FC<IAppProps> = (props: IAppProps) => {
    const [outdated, setOutDated] = useState<Boolean>(false);
    useEffect(() => {
        const req = `${url}&v=${props.version}`;
        fetch(req, {
            "headers": {
                "Content-Type": "application/json",
            }
        }).then(resp => resp.json()).then((res) => {
            appMeta['data'] = res?.data;
            setOutDated(res?.data?.outdated || false);
        })
    }, []);

    return (<>
    { outdated && <button>Get Latest Release</button>}
    </>)
    // const ref = props.storeRef;
    // return (<>
    //     <button onClick={() => {
    //     if (ref?.current) {
    //       console.log(ref.current.vizStore.exportAsRaw())
    //     }
    //   }}>Click Me</button>


    //   <textarea id="code"></textarea>
    //   <button onClick={() => {
    //     const txt = document.querySelector("#code")?.textContent || "";
    //     ref?.current?.vizStore.importRaw(txt);
    //   }}>Load</button>
    // </>)
}
export default Options;