import type { IRow, IMutField, IDataQueryPayload, IViewField, IChatMessage } from '@kanaries/graphic-walker/interfaces'
import type { IDarkMode, IThemeKey, IComputationFunction } from '@kanaries/graphic-walker/interfaces';

export interface IAppProps {
    // graphic-walker props
    fieldkeyGuard: boolean;
    themeKey: IThemeKey;
    dark: IDarkMode;
    // pygwalker props
    dataSource: IRow[];
    rawFields: IMutField[];
    id: string;
    dataSourceProps: IDataSourceProps;
    version?: string;
    hashcode?: string;
    visSpec: any;
    userConfig?: IUserConfig;
    env?: string;
    needLoadDatas?: boolean;
    specType: string;
    showCloudTool: boolean;
    enableAskViz: boolean;
    enableVlChat: boolean;
    needInitChart: boolean;
    useKernelCalc: boolean;
    useSaveTool: boolean;
    parseDslType: "server" | "client";
    communicationUrl: string;
    gwMode: "explore" | "renderer" | "filter_renderer" | "table";
    needLoadLastSpec: boolean;
    extraConfig?: any;
    fieldMetas: any;
    isExportDataFrame: boolean;
    defaultTab: "data" | "vis";
}

export interface IDataSourceProps {
    tunnelId: string;
    dataSourceId: string;
}

export interface IUserConfig {
    [key: string]: any;
    privacy: 'events' | 'update-only' | 'offline';
}

export interface ICommSqlQueryRequest {
    sql: string;
}

export interface ICommPayloadQueryRequest {
    payload: IDataQueryPayload;
}

export interface ICommBatchQueryRequest<TQuery> {
    queryList: TQuery[];
}

export interface ICommUpdateSpecRequest {
    visSpec: any[];
    chartData: any;
    workflowList?: any[];
}

export interface ICommUploadSpecToCloudRequest {
    fileName: string;
    newToken?: string;
}

export interface ICommChartImageRequest {
    rowIndex: number;
    colIndex: number;
    data: string;
    height: number;
    width: number;
    canvasHeight: number;
    canvasWidth: number;
}

export interface ICommSaveChartRequest {
    charts: ICommChartImageRequest[];
    singleChart: string;
    nRows: number;
    nCols: number;
    title: string;
}

export interface ICommAskSpecRequest {
    metas: IViewField[];
    query: string;
}

export interface ICommChatChartRequest {
    metas: IViewField[];
    chats: IChatMessage[];
}

export interface ICommOpenDesktopRequest {
    spec: any[];
    fields: any[];
}

export interface ICommUploadCloudChartRequest {
    chartName: string;
    datasetName: string;
    isPublic: boolean;
    visSpec: any[];
    workflow: any[];
}

export interface ICommUploadCloudDashboardRequest {
    chartName: string;
    datasetName: string;
    isPublic: boolean;
    isCreateDashboard: boolean;
    visSpec: any[];
    workflowList: any[][];
}

export interface ICommResponse<TData = any> {
    data?: TData;
    message?: string;
    code: number;
}

export interface ICommLatestVisSpecResponse {
    visSpec: any[];
}

export interface ICommDataRowsResponse {
    datas: IRow[];
}

export interface ICommBatchDataRowsResponse {
    datas: IRow[][];
}

export interface ICommUploadSpecToCloudResponse {
    specFilePath: string;
}

export interface ICommCloudCallbackResponse {
    data: any;
}

export interface ICommUploadCloudChartResponse {
    chartId: string;
    datasetId: string;
}

export interface ICommUploadCloudDashboardResponse {
    dashboardId: string;
    datasetId: string;
}
