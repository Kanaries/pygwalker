import React from "react";
import Modal from "../modal";
import { observer } from "mobx-react-lite";

import commonStore from "../../store/common";


interface ILoadDataModal {}

const LoadDataModal: React.FC<ILoadDataModal> = observer((props) => {

    

    return (
        <Modal
            show={commonStore.loadDataModalOpen}
            hideClose={true}
        >
            <div>
                <div className="flex justify-between mb-1">
                    <span className="text-base font-medium text-blue-700 dark:text-white">Loading Data</span>
                    <span className="text-sm font-medium text-blue-700 dark:text-white">
                        { commonStore.loadDataModalInfo.curIndex } / { commonStore.loadDataModalInfo.total }
                    </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                    <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${Math.floor(commonStore.loadDataModalInfo.curIndex/commonStore.loadDataModalInfo.total*100)}%` }}></div>
                </div>
            </div>
        </Modal>
    );
});

export default LoadDataModal;
