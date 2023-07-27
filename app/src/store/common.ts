import { makeObservable, observable, action } from 'mobx';

interface IInitModalInfo {
    total: number;
    curIndex: number;
    title: string;
}

class CommonStore {
    initModalOpen: boolean = false;
    initModalInfo: IInitModalInfo = {
        total: 0,
        curIndex: 0,
        title: "",
    };
    showCloudTool: boolean = false;
    version: string = "";

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

    constructor() {
        makeObservable(this, {
            initModalOpen: observable,
            initModalInfo: observable,
            showCloudTool: observable,
            version: observable,
            setInitModalOpen: action,
            setInitModalInfo: action,
            setShowCloudTool: action,
            setVersion: action
        });
    }
}

const commonStore = new CommonStore();

export default commonStore;