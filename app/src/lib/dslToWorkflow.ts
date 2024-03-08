import { chartToWorkflow } from '@kanaries/graphic-walker/src/utils/workflow';

export default function Transform(str: string) {
    return JSON.stringify(chartToWorkflow(JSON.parse(str)));
}
