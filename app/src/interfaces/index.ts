import type { IRow, IMutField } from '@kanaries/graphic-walker/dist/interfaces'
import type { IDarkMode, IThemeKey, IComputationFunction } from '@kanaries/graphic-walker/dist/interfaces';

export interface IAppProps {
    // graphic-walker props
    hideDataSourceConfig: boolean;
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
    needInitChart: boolean;
    useKernelCalc: boolean;
    useSaveTool: boolean;
    parseDslType: "server" | "client";
    communicationUrl: string;
    gwMode: "explore" | "renderer" | "filter_renderer";
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
