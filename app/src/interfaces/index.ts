import type { IGWProps } from '@kanaries/graphic-walker/dist/App'

export interface IAppProps extends IGWProps {
    id: string;
    dataSourceProps: IDataSourceProps;
    version?: string;
    hashcode?: string;
    visSpec?: string;
    userConfig?: IUserConfig;
    env?: string;
    needLoadDatas?: boolean;
    specType?: string;
    showCloudTool: boolean;
    needInitChart: boolean;
}

export interface IDataSourceProps {
    tunnelId: string;
    dataSourceId: string;
}

export interface IUserConfig {
    [key: string]: any;
    privacy: 'offline' | 'get-only' | 'meta' | 'any';
}