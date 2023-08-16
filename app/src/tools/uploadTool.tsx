import React, { useState, ReactElement } from 'react';
import { useNotification } from "../notify";
import communicationStore from "../store/communication"

import { ArrowUpCircleIcon } from '@heroicons/react/24/outline';
import LoadingIcon from '../components/loadingIcon';

import type { IAppProps } from '../interfaces';
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/dist/components/toolbar/toolbar-button"
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'

export function getUploadTool(
    props: IAppProps,
    storeRef: React.MutableRefObject<IGlobalStore | null>
) : ToolbarButtonItem {
    const [uploading, setUploading] = useState(false);
    const { notify } = useNotification();

    const noApiKeyTips = <>
        <p>Please set kanaries_api_key first.</p>
        <p>If you are not kanaries user, please register it from:</p>
        <p><a className='font-semibold' href='https://kanaries.net/home/access' target="_blank" >https://kanaries.net/home/access</a></p>
        <p>If you are kanaries user, please get your api key from:</p>
        <p><a className='font-semibold' href='https://kanaries.net/app/u/MarilynMonroe' target="_blank" >https://kanaries.net/app/u/MarilynMonroe</a></p>
        <p>, then go workspace detail page to get it.</p>
    </>

    const uploadSuccess = (shareUrl: string) => {
        notify({
            type: "success",
            title: "Success",
            message: <>
                <a className='font-semibold' href={shareUrl} target="_blank" >{shareUrl}</a>
            </>,
        }, 30_000);
    }

    const uploadFailed = (errorMsg: string | ReactElement) => {
        notify({
            type: "error",
            title: "Error",
            message: errorMsg,
        }, 30_000);
    }

    const onClick = async () => {
        if (props.specType !== "json_file") {
            notify({
                type: "warning",
                title: "Tips",
                message: "spec params is not 'json_file', save is not supported.",
            }, 4_000)
            return
        }
        if (uploading) return;
        setUploading(true);

        const resp = await communicationStore.comm?.sendMsg("upload_charts", {
            "visSpec": JSON.stringify(storeRef.current?.vizStore.exportViewSpec()!)
        });
        if (resp?.success) {
            uploadSuccess(resp.data?.shareUrl);
        } else {
            const msg = resp?.message === "no_kanaries_api_key" ? noApiKeyTips : resp?.message;
            uploadFailed(msg!);
        }
        setUploading(false);
    }

    return {
        key: "upload_charts",
        label: "upload_charts",
        icon: (iconProps?: any) => {
            return uploading ? <LoadingIcon width={36} height={36} /> : <ArrowUpCircleIcon {...iconProps} />
        },
        onClick: onClick,
    }
}
