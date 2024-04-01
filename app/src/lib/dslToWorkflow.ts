import { chartToWorkflow } from "@kanaries/graphic-walker/utils/workflow";

export default function Transform(str: string) {
    console.log({ str })
    return JSON.stringify(chartToWorkflow(JSON.parse(str)));
}
