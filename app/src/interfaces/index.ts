// import type { IGWProps } from '../../../graphic-walker/packages/graphic-walker/dist/App'
import type { IGWProps } from '@kanaries/graphic-walker/dist/App'

export interface IAppProps extends IGWProps {
    dataSourceProps: IDataSourceProps;
    version?: string;
    hashcode?: string;
    visSpec?: string;
    userConfig?: IUserConfig;
}

export interface IDataSourceProps {
    tunnelId: string;
    dataSourceId: string;
}

export interface IUserConfig {
    [key: string]: any;
    privacy: 'offline' | 'get-only' | 'meta' | 'any';
}