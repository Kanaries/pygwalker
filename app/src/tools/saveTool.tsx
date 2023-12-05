import React, { useEffect, useState } from 'react';
import communicationStore from "../store/communication"
import commonStore from '../store/common';
import { formatExportedChartDatas, getTimezoneOffsetSeconds } from "../utils/save"
import { checkUploadPrivacy } from '../utils/userConfig';

import { chartToWorkflow } from "@kanaries/graphic-walker"
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import LoadingIcon from '../components/loadingIcon';

import type { IAppProps } from '../interfaces';
import type { IGWHandler } from '@kanaries/graphic-walker/dist/interfaces';
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/dist/components/toolbar/toolbar-button"
import type { VizSpecStore } from '@kanaries/graphic-walker/dist/store/visualSpecStore'

function saveJupyterNotebook() {
    const rootDocument = window.parent.document;
    rootDocument.body.dispatchEvent(new KeyboardEvent('keydown', {key:'s', keyCode: 83, metaKey: true}));
    rootDocument.body.dispatchEvent(new KeyboardEvent('keydown', {key:'s', keyCode: 83, ctrlKey: true}));
}

export function hidePreview(id: string) {
    setTimeout(() => {
        window.parent.document.getElementById(`pygwalker-preview-${id}`)?.remove();
    }, 500)
}

export function getSaveTool(
    props: IAppProps,
    gwRef: React.MutableRefObject<IGWHandler | null>,
    storeRef: React.MutableRefObject<VizSpecStore | null>
) : ToolbarButtonItem {
    const [saving, setSaving] = useState(false);

    const saveSuccess = () => {
        commonStore.setNotification({
            type: "success",
            title: "Tips",
            message: "save success.",
        }, 4_000);

        setTimeout(() => {
            setSaving(false);
        }, 500);
    }

    const onClick = async () => {
        if (saving) return;
        setSaving(true);

        // if exportChart is undefined, it means that the chart is not reload, so we think dont need to save.
        if (gwRef.current?.exportChart === undefined) {
            saveSuccess();
            return;
        }
        let chartData = await gwRef.current?.exportChart!("data-url");
        try {
            const visSpec = storeRef.current?.exportCode();
            if (visSpec === undefined) {
                throw new Error("visSpec is undefined");
            }
            await communicationStore.comm?.sendMsg("update_spec", {
                "visSpec": visSpec,
                "chartData": await formatExportedChartDatas(chartData),
                "workflowList": visSpec.map((spec) => chartToWorkflow(spec)),
                "timezoneOffsetSeconds": getTimezoneOffsetSeconds(),
            });
            saveJupyterNotebook();
        } finally {
            setSaving(false);
            hidePreview(props.id);
        }
        
        if (["json_file", "json_ksf"].indexOf(props.specType) === -1) {
            if (checkUploadPrivacy() && commonStore.showCloudTool) {
                commonStore.setUploadSpecModalOpen(true);
            } else {
                commonStore.setNotification({
                    type: "warning",
                    title: "Tips",
                    message: "spec params is not 'json_file', save is not supported.",
                }, 4_000);
            }
        } else {
            saveSuccess();
        }
    }

    useEffect(() => {
        let locker = false;
        document.addEventListener("keydown", (event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === 's') {
                event.preventDefault();
                if (locker) return;
                locker = true;
                onClick().then(() => {
                    locker = false;
                });
            }
        });
    }, [])

    return {
        key: "save",
        label: "save",
        icon: (iconProps?: any) => {
            return saving ? <LoadingIcon width={36} height={36} /> : <DocumentTextIcon {...iconProps} />
        },
        onClick: onClick,
    }
}
