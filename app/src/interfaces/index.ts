import type { IGWProps } from '../../../graphic-walker/packages/graphic-walker/dist/App'

export interface IAppProps extends IGWProps {
    version?: string;
    hashcode?: string;
    visSpec?: string;
}