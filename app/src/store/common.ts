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

    setInitModalOpen(value: boolean) {
        this.initModalOpen = value;
    }

    setInitModalInfo(info: IInitModalInfo) {
        this.initModalInfo = info;
    }

    setShowCloudTool(value: boolean) {
        this.showCloudTool = value;
    }

    constructor() {
        makeObservable(this, {
            initModalOpen: observable,
            initModalInfo: observable,
            showCloudTool: observable,
            setInitModalOpen: action,
            setInitModalInfo: action,
            setShowCloudTool: action
        });
    }
}

const commonStore = new CommonStore();

export default commonStore;