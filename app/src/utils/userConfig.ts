import { IUserConfig } from "../interfaces";

let config: IUserConfig = {
    privacy: 'update-only',
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
