import { IUserConfig } from "../interfaces";

let config: IUserConfig = {
    privacy: 'meta',
};

export function checkUploadPrivacy() {
    return config.privacy === "meta" || config.privacy === "any";
}

export function setConfig(newConfig: IUserConfig) {
    config = newConfig;
}

export function getConfig() {
    return config;
}