import React, { useEffect, useState, useMemo } from 'react';
import communicationStore from "../store/communication"
import commonStore from '../store/common';
import { formatExportedChartDatas } from "../utils/save"
import { checkUploadPrivacy } from '../utils/userConfig';
import { tracker } from "@/utils/tracker";

import { chartToWorkflow } from "@kanaries/graphic-walker"
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import { Loader2 } from "lucide-react"

import type { IAppProps } from '../interfaces';
import { Button } from "@/components/ui/button"
import type { IGWHandler } from '@kanaries/graphic-walker/interfaces';
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button"
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore'

function DocumentTextIconWithRedPoint(iconProps) {
    return (
        <div style={{position: "relative"}} >
            <DocumentTextIcon {...iconProps} />
            <div style={{position: "absolute", top: "-2px", right: "-2px", width: "4px", height: "4px", borderRadius: "50%", backgroundColor: "red"}}></div>
        </div>
    )
}

export function getSaveTool(
    props: IAppProps,
    gwRef: React.MutableRefObject<IGWHandler | null>,
    storeRef: React.MutableRefObject<VizSpecStore | null>,
    isChanged: boolean,
    setIsChanged: React.Dispatch<React.SetStateAction<boolean>>
) : ToolbarButtonItem {
    const [saving, setSaving] = useState(false);

    const showUploadButton = useMemo(() => {
        return checkUploadPrivacy() && commonStore.showCloudTool;
    }, [commonStore.showCloudTool]);

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

    const onClick = async (where: string) => {
        if (saving) return;
        setSaving(true);
        tracker.track("click", {"entity": `save_${where}`, "spec_type": props.specType})

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
            if (storeRef.current?.visIndex !== undefined) {
                const currentChart = visSpec[storeRef.current?.visIndex];
                if (currentChart.layout.size.mode === "auto") {
                    currentChart.layout.size.width = chartData.container()?.clientWidth || 320;
                    currentChart.layout.size.height = chartData.container()?.clientHeight || 200;
                }
            }
            await communicationStore.comm?.sendMsg("update_spec", {
                "visSpec": visSpec,
                "chartData": await formatExportedChartDatas(chartData),
                "workflowList": visSpec.map((spec) => chartToWorkflow(spec))
            });
        } finally {
            setSaving(false);
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
            setIsChanged(false);
            saveSuccess();
        }
    }

    const onClickUpload = () => {
        commonStore.setUploadChartModalOpen(true);
        tracker.track("click", {"entity": "save_icon_form_upload", "spec_type": props.specType});
    }

    useEffect(() => {
        let locker = false;
        document.addEventListener("keydown", (event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === 's') {
                event.preventDefault();
                if (locker) return;
                locker = true;
                onClick("from_keyboard").then(() => {
                    locker = false;
                });
            }
        });
    }, [])

    return {
        key: "save",
        label: "save",
        icon: (iconProps?: any) => {
            if (saving) return <Loader2 className='animate-spin' />;
            return isChanged ? <DocumentTextIconWithRedPoint {...iconProps} /> :  <DocumentTextIcon {...iconProps} />
        },
        form: (
            <div className='flex flex-col'>
                <Button variant="ghost" aria-label="save spec" onClick={() => onClick("icon_form_save")}>
                    save spec
                </Button>
                {showUploadButton && (
                    <Button variant="ghost" aria-label="upload chart" onClick={onClickUpload}>
                        upload chart
                    </Button>
                )}
            </div>
        ),
        onClick: () => onClick("icon"),
    }
}
