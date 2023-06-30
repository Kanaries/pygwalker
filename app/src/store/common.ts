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

    setLoadDataModalOpen(value: boolean) {
        this.loadDataModalOpen = value;
    }

    setLoadDataModalInfo(info: ILoadDataModalInfo) {
        this.loadDataModalInfo = info;
    }

    constructor() {
        makeObservable(this, {
            loadDataModalOpen: observable,
            loadDataModalInfo: observable,
            setLoadDataModalOpen: action,
            setLoadDataModalInfo: action
        });
    }
}

const commonStore = new CommonStore();

export default commonStore;