import React, { useState, useEffect } from "react";
import { observer } from "mobx-react-lite";
import type { IGWHandler } from "@kanaries/graphic-walker/interfaces";
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore'
import { chartToWorkflow } from "@kanaries/graphic-walker"
import { tracker } from "@/utils/tracker";

import communicationStore from "../../store/communication";
import commonStore from "../../store/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

interface IUploadChartModal {
    gwRef: React.MutableRefObject<IGWHandler | null>;
    storeRef: React.MutableRefObject<VizSpecStore | null>;
    dark: string;
}

const UploadChartModal: React.FC<IUploadChartModal> = observer((props) => {
    const [uploading, setUploading] = useState(false);
    const [chartName, setChartName] = useState("");
    const [datasetName, setDatasetName] = useState("");
    const [isPublic, setIsPublic] = useState(true);
    const [isCreateDashboard, setIsCreateDashboard] = useState(true);
    const [instanceType, setInstanceType] = useState("");

    useEffect(() => {
        if (commonStore.uploadChartModalOpen) {
            const instanceType = (props.storeRef.current?.exportCode().length || 0) > 1 ? "dashboard" : "chart";
            setChartName(`${instanceType}-${new Date().getTime().toString(16).padStart(16, "0")}`);
            setDatasetName(`dataset-${new Date().getTime().toString(16).padStart(16, "0")}`);
            setIsPublic(true);
            setInstanceType(instanceType);
        }
    }, [commonStore.uploadChartModalOpen])

    const uploadSuccess = (instanceType: string, instanceId: string, datasetId: string) => {
        const managerUrl = instanceType === "chart" ? `https://kanaries.net/analytics/c/${instanceId}` : `https://kanaries.net/analytics/d/${instanceId}`
        const shareUrl = instanceType === "chart" ? `https://kanaries.net/analytics/chart/${instanceId}/share?theme=${props.dark}` : `https://kanaries.net/analytics/dashboard/${instanceId}/share?theme=${props.dark}`
        const datsetUrl = `https://kanaries.net/analytics/detail/${datasetId}`
        if (instanceType === "dashboard" && instanceId === "" ) {
            commonStore.setNotification(
                {
                    type: "success",
                    title: "Success",
                    message: (
                        <>
                            <p>Upload success, you can view and manager it at:
                                <a className="font-semibold" href={datsetUrl} target="_blank">
                                    {datsetUrl}
                                </a>
                            </p>
                        </>
                    ),
                },
                30_000
            );
        } else {
            commonStore.setNotification(
                {
                    type: "success",
                    title: "Success",
                    message: (
                        <>
                            <p>Upload success, you can view and manager it at:
                                <a className="font-semibold" href={managerUrl} target="_blank">
                                    {managerUrl}
                                </a>
                            </p>
                            <br />
                            {isPublic && <p>Since you set the {instanceType} to public, you can also share it with others by:
                                <a className="font-semibold" href={shareUrl} target="_blank">
                                    {shareUrl}
                                </a>
                            </p>}
                        </>
                    ),
                },
                30_000
            );
        }
    };

    const onClick = async () => {
        if (uploading) return;
        setUploading(true);
        tracker.track("click", {"entity": "upload_chart_button"});

        const visSpec = props.storeRef.current?.exportCode()!;
        try {
            if (instanceType === "dashboard") {
                const resp = await communicationStore.comm?.sendMsg(
                    "upload_to_cloud_dashboard",
                    {
                        chartName: chartName,
                        datasetName: datasetName,
                        isPublic: isPublic,
                        isCreateDashboard: isCreateDashboard,
                        visSpec: visSpec,
                        workflowList: visSpec.map(spec => chartToWorkflow(spec).workflow),
                    },
                    120_000
                );
                uploadSuccess(instanceType, resp?.data.dashboardId, resp?.data.datasetId);
            } else {
                const resp = await communicationStore.comm?.sendMsg(
                    "upload_to_cloud_charts",
                    {
                        chartName: chartName,
                        datasetName: datasetName,
                        isPublic: isPublic,
                        visSpec: visSpec,
                        workflow: chartToWorkflow(visSpec[0]).workflow,
                    },
                    120_000
                );
                uploadSuccess(instanceType, resp?.data.chartId, resp?.data.datasetId);
            }
            commonStore.setUploadChartModalOpen(false);
        } finally {
            setUploading(false);
        }
    };

    return (
        <Dialog
            open={commonStore.uploadChartModalOpen}
            modal={false}
            onOpenChange={(show) => {
                commonStore.setUploadChartModalOpen(show)
            }}
        >
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Upload Chart</DialogTitle>
                    <DialogDescription>
                        upload your charts to dashboard of kanaries cloud.
                    </DialogDescription>
                </DialogHeader>
                <div>
                    <div className="text-sm max-h-64 overflow-auto p-1 flex flex-col space-y-2">
                        <div className="grid w-full max-w-sm items-center gap-1.5">
                            <Label htmlFor="dataset-name-input">Dataset Name</Label>
                            <Input
                                value={datasetName}
                                onChange={(e) => {
                                    setDatasetName(e.target.value);
                                }}
                                type="text"
                                placeholder="please input dataset name"
                                id="dataset-name-input"
                                className="mb-1"
                            />
                        </div>
                        <div className="grid w-full max-w-sm items-center gap-1.5">
                            <Label htmlFor="chart-name-input">
                                {instanceType === "dashboard" ? "Dashboard Name" : "Chart Name"}
                            </Label>
                            <Input
                                value={chartName}
                                onChange={(e) => {
                                    setChartName(e.target.value);
                                }}
                                disabled={!isCreateDashboard}
                                type="text"
                                placeholder="please input chart name"
                                id="chart-name-input"
                                className="mb-1"
                            />
                        </div>
                        <div className="items-top flex space-x-2">
                            <Checkbox
                                id="public-checkbox"
                                checked={isPublic}
                                onCheckedChange={(checked) => {setIsPublic(checked as boolean);}}
                            />
                            <div className="grid gap-1.5 leading-none">
                                <Label htmlFor="public-checkbox">Is Public?</Label>
                                <p className="text-sm text-muted-foreground">
                                    Make {instanceType} publicly accessible.
                                </p>
                            </div>
                        </div>
                        {instanceType === "dashboard" && (
                            <div className="items-top flex space-x-2">
                                <Checkbox
                                    id="create-dashboard-checkbox"
                                    checked={isCreateDashboard}
                                    onCheckedChange={(checked) => {setIsCreateDashboard(checked as boolean);}}
                                />
                                <div className="grid gap-1.5 leading-none">
                                    <Label htmlFor="create-dashboard-checkbox">Create Dashboard?</Label>
                                    <p className="text-sm text-muted-foreground">
                                        Create a dashboard containing all charts, or upload charts individually.
                                    </p>
                                </div>
                            </div>
                        )}
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
