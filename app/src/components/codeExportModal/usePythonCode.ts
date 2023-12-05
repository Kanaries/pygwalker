import { getTimezoneOffsetSeconds } from "@/utils/save";
import { chartToWorkflow } from "@kanaries/graphic-walker";
import { IChartForExport } from "@kanaries/graphic-walker/dist/interfaces";
import { useMemo } from "react"

export function usePythonCode (props: {
    sourceCode: string;
    visSpec: IChartForExport[];
    version: string;
}) {
    const { sourceCode, visSpec, version } = props;
    const pygConfig = useMemo(() => {
        return JSON.stringify({
            "config": visSpec,
            "chart_map": {},
            "workflow_list": visSpec.map((spec) => chartToWorkflow(spec)),
            "timezoneOffsetSeconds": getTimezoneOffsetSeconds(),
            version
        })
    }, [visSpec])
    const pyCode = useMemo(() => {
        const preCode = sourceCode.replace("'____pyg_walker_spec_params____'", "vis_spec")
        return `vis_spec = r"""${pygConfig}"""\n${preCode}`;
    }, [sourceCode, pygConfig])
    return {
        pyCode
    }
}