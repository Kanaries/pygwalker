import React, { useState, useEffect } from "react";
import { observer } from "mobx-react-lite";
import type { IGWHandler } from "@kanaries/graphic-walker/dist/interfaces";
import type { VizSpecStore } from '@kanaries/graphic-walker/dist/store/visualSpecStore'
import { chartToWorkflow } from "@kanaries/graphic-walker"

import communicationStore from "../../store/communication";
import commonStore from "../../store/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface IUploadChartModal {
    gwRef: React.MutableRefObject<IGWHandler | null>;
    storeRef: React.MutableRefObject<VizSpecStore | null>;
    open: boolean;
    setOpen: (open: boolean) => void;
}

const UploadChartModal: React.FC<IUploadChartModal> = observer((props) => {
    const [uploading, setUploading] = useState(false);
    const [chartName, setChartName] = useState("");
    const [datasetName, setDatasetName] = useState("");
    const [isPublic, setIsPublic] = useState(true);

    useEffect(() => {
        if (props.open) {
            setChartName(`chart-${new Date().getTime().toString(16).padStart(16, "0")}`);
            setDatasetName(`dataset-${new Date().getTime().toString(16).padStart(16, "0")}`);
            setIsPublic(true);
        }
    }, [props.open])

    const uploadSuccess = (chartId: string) => {
        const chartUrl = `https://kanaries.net/app/data-infra/c/${chartId}`
        const shareUrl = `https://kanaries.net/app/data-infra/chart/${chartId}/share`
        commonStore.setNotification(
            {
                type: "success",
                title: "Success",
                message: (
                    <>
                        <p>Upload success, you can view and manager it at:
                            <a className="font-semibold" href={chartUrl} target="_blank">
                                {chartUrl}
                            </a>
                        </p>
                        <br />
                        {isPublic && <p>Since you set the chart to public, you can also share it with others by:
                            <a className="font-semibold" href={shareUrl} target="_blank">
                                {shareUrl}
                            </a>
                        </p>}
                    </>
                ),
            },
            30_000
        );
    };

    const onClick = async () => {
        if (uploading) return;
        setUploading(true);

        const visSpec = props.storeRef.current?.exportCode()!;
        try {
            const resp = await communicationStore.comm?.sendMsg(
                "upload_to_cloud_charts",
                {
                    chartName: chartName,
                    datasetName: datasetName,
                    isPublic: isPublic,
                    visSpec: visSpec,
                    workflowList: chartToWorkflow(visSpec[0]).workflow,
                },
                120_000
            );
            props.setOpen(false);
            uploadSuccess(resp?.data.chartId);
        } finally {
            setUploading(false);
        }
    };

    return (
        <Dialog
            open={props.open}
            modal={false}
            onOpenChange={(show) => {
                props.setOpen(show);
            }}
        >
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Upload Chart</DialogTitle>
                    <DialogDescription>
                        upload your charts to kanaries cloud.
                    </DialogDescription>
                </DialogHeader>
                <div>
                    <div className="text-sm max-h-64 overflow-auto">
                        <label className="block text-gray-700 text-sm font-bold mb-2">
                            Chart Name
                        </label>
                        <input
                            value={chartName}
                            onChange={(e) => {
                                setChartName(e.target.value);
                            }}
                            type="text"
                            placeholder="please input chart name"
                            id="chart-name-input"
                            className="mb-2 block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                        />
                        <label className="block text-gray-700 text-sm font-bold mb-2">
                            Dataset Name
                        </label>
                        <input
                            value={datasetName}
                            onChange={(e) => {
                                setDatasetName(e.target.value);
                            }}
                            type="text"
                            placeholder="please input dataset name"
                            id="dataset-name-input"
                            className="mb-2 block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                        />
                        <div className="flex items-center justify-end mt-2">
                            <input
                                id="link-checkbox"
                                type="checkbox"
                                checked={isPublic}
                                onChange={(e) => {
                                    setIsPublic(e.target.checked);
                                }}
                                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                            />
                            <label className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">Is Public?</label>
                        </div>
                    </div>
                    <div className="mt-4 flex justify-end">
                        <Button variant="outline" className="mr-2 px-6" disabled={uploading} onClick={onClick}>
                            {uploading ? "uploading.." : "upload"}
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
});

export default UploadChartModal;
