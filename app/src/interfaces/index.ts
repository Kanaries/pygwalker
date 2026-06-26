import type { IRow, IMutField } from '@kanaries/graphic-walker/interfaces'
import type { IDarkMode, IThemeKey, IComputationFunction } from '@kanaries/graphic-walker/interfaces';

export type {
    ICommAction,
    ICommAskSpecRequest,
    ICommBatchDataRowsResponse,
    ICommBatchQueryRequest,
    ICommChartImageRequest,
    ICommChatChartRequest,
    ICommCloudCallbackResponse,
    ICommDataRowsResponse,
    ICommEmptyRequest,
    ICommEmptyResponse,
    ICommEnvelope,
    ICommLatestVisSpecResponse,
    ICommOpenDesktopRequest,
    ICommPayloadQueryRequest,
    ICommRequestEnvelope,
    ICommRequestMap,
    ICommResponse,
    ICommResponseEnvelope,
    ICommResponseMap,
    ICommSaveChartRequest,
    ICommSqlQueryRequest,
    ICommUpdateSpecRequest,
    ICommUploadCloudChartRequest,
    ICommUploadCloudDashboardRequest,
    ICommUploadSpecToCloudRequest,
} from './comm.generated';

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
    len: number;
    version?: string;
    hashcode?: string;
    visSpec: any;
    userConfig?: IUserConfig;
    env?: string;
    sourceInvokeCode: string;
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
    datasetType: string;
    extraConfig?: any;
    fieldMetas: any;
    isExportDataFrame: boolean;
    defaultTab: "data" | "vis";
    useCloudCalc: boolean;
    __comm?: any;
}

export interface IDataSourceProps {
    tunnelId: string;
    dataSourceId: string;
}

export interface IUserConfig {
    [key: string]: any;
    privacy: 'events' | 'update-only' | 'offline';
}
