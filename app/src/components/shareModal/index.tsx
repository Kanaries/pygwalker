import React, { useState, ReactElement, useEffect } from 'react';
import { observer } from "mobx-react-lite";
import communicationStore from "../../store/communication";
import commonStore from "../../store/common";
import DefaultButton from "../button/default";
import Modal from "../modal";
import { formatExportedChartDatas } from "../../utils/save"

import type { IGWHandler } from '@kanaries/graphic-walker/dist/interfaces';
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'


interface IShareModal {
    gwRef: React.MutableRefObject<IGWHandler | null>,
    storeRef: React.MutableRefObject<IGlobalStore | null>
    open: boolean;
    setOpen: (open: boolean) => void;
}

const ShareModal: React.FC<IShareModal> = observer((props) => {
    const [ sharing, setSharing ] = useState(false);
    const [ name, setName ] = useState("");
    const [ isNewNotebook, setIsNewNotebook ] = useState(true);

    useEffect(() => {
        if (props.open) {
            const curIndex = props.storeRef.current?.vizStore.visIndex!;
            setName(props.storeRef.current?.vizStore.exportViewSpec()![curIndex].name!);
        }
    }, [props.open]);

    const shareSuccess = (shareUrl: string) => {
        commonStore.setNotification({
            type: "success",
            title: "Success",
            message: <>
                <a className='font-semibold' href={shareUrl} target="_blank" >{shareUrl}</a>
            </>,
        }, 30_000);
    }

    const shareFailed = (errorMsg: string | ReactElement) => {
        commonStore.setNotification({
            type: "error",
            title: "Error",
            message: errorMsg,
        }, 30_000);
    }

    const onClick = async () => {
        if (sharing) return;
        setSharing(true);

        let chartData = await props.gwRef.current?.exportChart!("data-url");
        const resp = await communicationStore.comm?.sendMsg("upload_charts", {
            "chartName": name,
            "newNotebook": isNewNotebook,
            "visSpec": JSON.stringify(props.storeRef.current?.vizStore.exportViewSpec()!),
            "chartData": await formatExportedChartDatas(chartData!),
        }, 120_000);
        if (resp?.success) {
            props.setOpen(false);
            shareSuccess(resp.data?.shareUrl);
        } else {
            shareFailed(resp?.message!);
        }
        setSharing(false);
    }

    return (
        <Modal
            show={props.open}
            onClose={() => {
                props.setOpen(false);
            }}
        >
            <div>
                <h1 className="mb-4">Share</h1>
                <div className="text-sm max-h-64 overflow-auto">
                    <input
                        value={name}
                        onChange={(e) => { setName(e.target.value) }}
                        type="text"
                        placeholder='please input chart name'
                        id="chart-name-input"
                        className="block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                    />
                    <div className="flex items-center justify-end mt-2">
                        <input id="link-checkbox" type="checkbox" checked={isNewNotebook} onChange={(e) => {setIsNewNotebook(e.target.checked)}} className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600" />
                        <label className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">
                            Auto create kanaries notebook?
                        </label>
                    </div>
                </div>
                <div className="mt-4 flex justify-end">
                    <DefaultButton
                        text={sharing ? "sharing.." : "share"}
                        className="mr-2 px-6"
                        disabled={sharing}
                        onClick={onClick}
                    />
                </div>
            </div>
        </Modal>
    );
});

export default ShareModal;
