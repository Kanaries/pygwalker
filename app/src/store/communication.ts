import { makeObservable, observable, action } from 'mobx';
import { ICommunication } from '../utils/communication';

class CommunicationStore {
    comm: ICommunication | null = null;

    setComm(comm: ICommunication) {
        this.comm = comm;
    }

    constructor() {
        makeObservable(this, {
            comm: observable,
            setComm: action,
        });
    }
}

const communicationStore = new CommunicationStore();

export default communicationStore;