import * as htmlToImage from 'html-to-image';
import type { IChartExportResult } from '@kanaries/graphic-walker/interfaces';

export function download(data: string, filename: string, type: string) {
    var file = new Blob([data], { type: type });
    // @ts-ignore
    if (window.navigator.msSaveOrOpenBlob)
        // IE10+
        // @ts-ignore
        window.navigator.msSaveOrOpenBlob(file, filename);
    else {
        // Others
        var a = document.createElement("a"),
            url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function () {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 0);
    }
}

export async function formatExportedChartDatas(chartData: IChartExportResult) {
    const chartDom = chartData.container();
    if (chartDom === null) {
        return {
            ...chartData,
            singleChart: ""
        };
    }
    // export png don't support geo chart
    if (chartData.charts.length === 0) {
        return {
            ...chartData,
            nCols: 1,
            nRows: 1,
            charts: [{
                colIndex: 0,
                rowIndex: 0,
                width: chartDom?.clientWidth,
                height: chartDom?.clientHeight,
                canvasWidth: chartDom?.clientWidth,
                canvasHeight: chartDom?.clientHeight,
                data: "",
                canvas: () => null
            }],
            singleChart: ""
        }
    } else {
        const singleChart = await htmlToImage.toPng(
            chartDom!,
            {width: chartDom?.scrollWidth, height: chartDom?.scrollHeight}
        )
        return {
            ...chartData,
            singleChart
        }
    }
}

export function getTimezoneOffsetSeconds(): number {
    return -new Date().getTimezoneOffset() * 60;
}
