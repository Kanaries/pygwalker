import { makeObservable, observable, action } from 'mobx';
import { ReactElement } from "react";

interface IInitModalInfo {
    total: number;
    curIndex: number;
    title: string;
}

export interface INotification {
    title: string;
    message: string | ReactElement;
    type: "success" | "error" | "info" | "warning";
}

class CommonStore {
    _notifyTimeoutFunc = setTimeout(() => {}, 0);

    initModalOpen: boolean = false;
    initModalInfo: IInitModalInfo = {
        total: 0,
        curIndex: 0,
        title: "",
    };
    showCloudTool: boolean = false;
    version: string = "";
    notification: INotification | null = null;

    setInitModalOpen(value: boolean) {
        this.initModalOpen = value;
    }

    setInitModalInfo(info: IInitModalInfo) {
        this.initModalInfo = info;
    }

    setShowCloudTool(value: boolean) {
        this.showCloudTool = value;
    }

    setVersion(value: string) {
        this.version = value;
    }
    
    setNotification(value: INotification | null, timeout: number = 5_000) {
        clearTimeout(this._notifyTimeoutFunc);
        this.notification = value;
        this._notifyTimeoutFunc = setTimeout(() => {
            this.notification = null;
        }, timeout);
    }

    constructor() {
        makeObservable(this, {
            initModalOpen: observable,
            initModalInfo: observable,
            showCloudTool: observable,
            version: observable,
            notification: observable,
            setInitModalOpen: action,
            setInitModalInfo: action,
            setShowCloudTool: action,
            setVersion: action,
            setNotification: action,
        });
    }
}

const commonStore = new CommonStore();

export default commonStore;