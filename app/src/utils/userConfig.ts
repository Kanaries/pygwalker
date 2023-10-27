import { IUserConfig } from "../interfaces";

let config: IUserConfig = {
    privacy: 'events',
};

export function checkUploadPrivacy() {
    return config.privacy !== "offline";
}

export function setConfig(newConfig: IUserConfig) {
    config = newConfig;
}

export function getConfig() {
    return config;
}