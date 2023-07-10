import { makeObservable, observable, action } from 'mobx';

interface ILoadDataModalInfo {
    total: number;
    curIndex: number;
}

class CommonStore {
    loadDataModalOpen: boolean = false;
    loadDataModalInfo: ILoadDataModalInfo = {
        total: 0,
        curIndex: 0
    };
    showCloudTool: boolean = false;

    setLoadDataModalOpen(value: boolean) {
        this.loadDataModalOpen = value;
    }

    setLoadDataModalInfo(info: ILoadDataModalInfo) {
        this.loadDataModalInfo = info;
    }

    setShowCloudTool(value: boolean) {
        this.showCloudTool = value;
    }

    constructor() {
        makeObservable(this, {
            loadDataModalOpen: observable,
            loadDataModalInfo: observable,
            showCloudTool: observable,
            setLoadDataModalOpen: action,
            setLoadDataModalInfo: action,
            setShowCloudTool: action
        });
    }
}

const commonStore = new CommonStore();

export default commonStore;