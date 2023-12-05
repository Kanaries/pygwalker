import type { IRow, IMutField } from '@kanaries/graphic-walker/dist/interfaces'

export interface IAppProps {
    // graphic-walker props
    hideDataSourceConfig: boolean;
    fieldkeyGuard: boolean;
    themeKey: string;
    dark: string;
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
    needInitChart: boolean;
    useKernelCalc: boolean;
    useSaveTool: boolean;
    parseDslType: "server" | "client";
    communicationUrl: string;
    gwMode: "explore" | "renderer";
    needLoadLastSpec: boolean;
    extraConfig?: any;
    fieldMetas: any;
    isExportDataFrame: boolean;
}

export interface IDataSourceProps {
    tunnelId: string;
    dataSourceId: string;
}

export interface IUserConfig {
    [key: string]: any;
    privacy: 'events' | 'update-only' | 'offline';
}