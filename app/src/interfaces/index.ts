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

export interface ICommEnvelope<TAction extends string = string, TData = any> {
    gid?: string;
    rid?: string;
    action: TAction;
    data: TData;
}

export interface ICommEmptyResponse {}

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

export interface ICommRequestMap {
    ping: ICommEmptyResponse;
    request_data: ICommEmptyResponse;
    get_latest_vis_spec: ICommEmptyResponse;
    save_chart: ICommSaveChartRequest;
    update_spec: ICommUpdateSpecRequest;
    upload_spec_to_cloud: ICommUploadSpecToCloudRequest;
    get_datas: ICommSqlQueryRequest;
    get_datas_by_payload: ICommPayloadQueryRequest;
    batch_get_datas_by_sql: ICommBatchQueryRequest<string>;
    batch_get_datas_by_payload: ICommBatchQueryRequest<IDataQueryPayload>;
    get_spec_by_text: ICommAskSpecRequest;
    get_chart_by_chats: ICommChatChartRequest;
    export_dataframe_by_payload: ICommPayloadQueryRequest;
    export_dataframe_by_sql: ICommSqlQueryRequest;
    upload_to_cloud_charts: ICommUploadCloudChartRequest;
    upload_to_cloud_dashboard: ICommUploadCloudDashboardRequest;
    open_in_desktop: ICommOpenDesktopRequest;
}

export interface ICommResponseMap {
    ping: ICommEmptyResponse;
    request_data: ICommEmptyResponse;
    get_latest_vis_spec: ICommLatestVisSpecResponse;
    save_chart: ICommEmptyResponse;
    update_spec: ICommEmptyResponse;
    upload_spec_to_cloud: ICommUploadSpecToCloudResponse;
    get_datas: ICommDataRowsResponse;
    get_datas_by_payload: ICommDataRowsResponse;
    batch_get_datas_by_sql: ICommBatchDataRowsResponse;
    batch_get_datas_by_payload: ICommBatchDataRowsResponse;
    get_spec_by_text: ICommCloudCallbackResponse;
    get_chart_by_chats: ICommCloudCallbackResponse;
    export_dataframe_by_payload: ICommEmptyResponse;
    export_dataframe_by_sql: ICommEmptyResponse;
    upload_to_cloud_charts: ICommUploadCloudChartResponse;
    upload_to_cloud_dashboard: ICommUploadCloudDashboardResponse;
    open_in_desktop: ICommEmptyResponse;
}

export type ICommAction = keyof ICommRequestMap;

export type ICommRequestEnvelope<TAction extends ICommAction> = ICommEnvelope<TAction, ICommRequestMap[TAction]>;

export type ICommResponseEnvelope<TData = any> = ICommEnvelope<"finish_request", ICommResponse<TData>>;
