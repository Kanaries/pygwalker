import React from "react";
import { observer } from "mobx-react-lite";
import { Dialog, DialogContent } from "@/components/ui/dialog";

import commonStore from "../../store/common";

interface IInitModal {}

const InitModal: React.FC<IInitModal> = observer((props) => {
    return (
        <Dialog open={commonStore.initModalOpen} modal={true}>
            <DialogContent hideClose>
                <div className="flex justify-between mb-1">
                    <span className="text-base font-medium text-blue-700 dark:text-white">{commonStore.initModalInfo.title}</span>
                    <span className="text-sm font-medium text-blue-700 dark:text-white">
                        {commonStore.initModalInfo.curIndex} / {commonStore.initModalInfo.total}
                    </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                    <div
                        className="bg-blue-600 h-2.5 rounded-full"
                        style={{ width: `${Math.floor((commonStore.initModalInfo.curIndex / commonStore.initModalInfo.total) * 100)}%` }}
                    ></div>
                </div>
            </DialogContent>
        </Dialog>
    );
});

export default InitModal;
