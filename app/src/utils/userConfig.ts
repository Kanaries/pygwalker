import { IUserConfig } from "../interfaces";

let config: IUserConfig = {
    privacy: 'meta',
};

export function setConfig(newConfig: IUserConfig) {
    config = newConfig;
}

export function getConfig() {
    return config;
}