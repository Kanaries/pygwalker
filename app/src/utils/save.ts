import * as htmlToImage from 'html-to-image';
import type { IChartExportResult } from '@kanaries/graphic-walker/interfaces';
import type { ICommChartImageRequest, ICommSaveChartRequest } from '../interfaces';

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

function toChartImageRequest(chart: IChartExportResult["charts"][number]): ICommChartImageRequest {
    return {
        rowIndex: chart.rowIndex,
        colIndex: chart.colIndex,
        data: chart.data,
        height: chart.height,
        width: chart.width,
        canvasHeight: chart.canvasHeight,
        canvasWidth: chart.canvasWidth
    };
}

function toSaveChartRequest(chartData: IChartExportResult, charts: ICommChartImageRequest[], singleChart: string): ICommSaveChartRequest {
    return {
        charts,
        singleChart,
        nRows: chartData.nRows,
        nCols: chartData.nCols,
        title: chartData.title
    };
}

export async function formatExportedChartDatas(chartData: IChartExportResult): Promise<ICommSaveChartRequest> {
    const chartDom = chartData.container();
    if (chartDom === null) {
        return toSaveChartRequest(chartData, chartData.charts.map(toChartImageRequest), "");
    }
    // export png don't support geo chart
    if (chartData.charts.length === 0) {
        return {
            charts: [{
                colIndex: 0,
                rowIndex: 0,
                width: chartDom.clientWidth,
                height: chartDom.clientHeight,
                canvasWidth: chartDom.clientWidth,
                canvasHeight: chartDom.clientHeight,
                data: "",
            }],
            singleChart: "",
            nCols: 1,
            nRows: 1,
            title: chartData.title
        }
    } else {
        const singleChart = await htmlToImage.toPng(
            chartDom!,
            {width: chartDom?.scrollWidth, height: chartDom?.scrollHeight}
        )
        return toSaveChartRequest(chartData, chartData.charts.map(toChartImageRequest), singleChart);
    }
}

export function getTimezoneOffsetSeconds(): number {
    return -new Date().getTimezoneOffset() * 60;
}
