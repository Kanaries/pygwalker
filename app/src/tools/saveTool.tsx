import React, { useEffect, useState } from 'react';
import { useNotification } from "../notify";
import communicationStore from "../store/communication"
import { encodeSpec } from "../utils/graphicWalkerParser"
import { domToPng } from "../utils/screenshot"

import { DocumentTextIcon } from '@heroicons/react/24/outline';
import LoadingIcon from '../components/loadingIcon';

import type { IAppProps } from '../interfaces';
import type { IGWHandler } from '@kanaries/graphic-walker/dist/interfaces';
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/dist/components/toolbar/toolbar-button"
import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'

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
    storeRef: React.MutableRefObject<IGlobalStore | null>
) : ToolbarButtonItem {
    const [saving, setSaving] = useState(false);
    const { notify } = useNotification();

    const saveSuccess = () => {
        notify({
            type: "success",
            title: "Tips",
            message: "save success.",
        }, 4_000);

        setTimeout(() => {
            setSaving(false);
        }, 500);
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
        if (saving) return;
        setSaving(true);

        // if exportChart is undefined, it means that the chart is not reload, so we think dont need to save.
        if (gwRef.current?.exportChart === undefined) {
            saveSuccess();
            return;
        }
        const chartData = await gwRef.current?.exportChart!("data-url");
        const singleChart = await domToPng(chartData.container()!);
        await communicationStore.comm?.sendMsg("update_spec", {
            "visSpec": encodeSpec(storeRef.current?.vizStore.exportViewSpec()!),
            "chartData": {...chartData, singleChart}
        });
        hidePreview(props.id);
        saveSuccess();
        saveJupyterNotebook();
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
