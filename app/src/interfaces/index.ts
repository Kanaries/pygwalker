import type { IRow, IMutField, IDataQueryPayload } from '@kanaries/graphic-walker/interfaces'
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
