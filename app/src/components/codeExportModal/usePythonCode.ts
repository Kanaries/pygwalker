import { IVisSpec } from "@kanaries/graphic-walker/dist/interfaces";
import { useMemo } from "react"

export function usePythonCode (props: {
    sourceCode: string;
    specList: IVisSpec[];
    version: string;
}) {
    const { sourceCode, specList, version } = props;
    const pygConfig = useMemo(() => {
        return JSON.stringify({
            "config": JSON.stringify(specList),
            "chart_map": {},
            version
        })
    }, [specList])
    const pyCode = useMemo(() => {
        const preCode = sourceCode.replace("'____pyg_walker_spec_params____'", "vis_spec")
        return `vis_spec = r"""${pygConfig}"""\n${preCode}`;
    }, [sourceCode, pygConfig])
    return {
        pyCode
    }
}