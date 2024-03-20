import React, { useState, useEffect } from "react";
import { observer } from "mobx-react-lite";
import type { IGWHandler } from "@kanaries/graphic-walker/interfaces";
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore'
import { chartToWorkflow } from "@kanaries/graphic-walker"

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
    open: boolean;
    dark: string;
    setOpen: (open: boolean) => void;
}

const UploadChartModal: React.FC<IUploadChartModal> = observer((props) => {
    const [uploading, setUploading] = useState(false);
    const [chartName, setChartName] = useState("");
    const [datasetName, setDatasetName] = useState("");
    const [isPublic, setIsPublic] = useState(true);

    useEffect(() => {
        if (props.open) {
            setChartName(`dashboard-${new Date().getTime().toString(16).padStart(16, "0")}`);
            setDatasetName(`dataset-${new Date().getTime().toString(16).padStart(16, "0")}`);
            setIsPublic(true);
        }
    }, [props.open])

    const uploadSuccess = (dashboardId: string) => {
        const dashboardUrl = `https://kanaries.net/app/data-infra/d/${dashboardId}`
        const shareUrl = `https://kanaries.net/app/data-infra/dashboard/${dashboardId}/share?theme=${props.dark}`
        commonStore.setNotification(
            {
                type: "success",
                title: "Success",
                message: (
                    <>
                        <p>Upload success, you can view and manager it at:
                            <a className="font-semibold" href={dashboardUrl} target="_blank">
                                {dashboardUrl}
                            </a>
                        </p>
                        <br />
                        {isPublic && <p>Since you set the dashboard to public, you can also share it with others by:
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
                "upload_to_cloud_dashboard",
                {
                    chartName: chartName,
                    datasetName: datasetName,
                    isPublic: isPublic,
                    visSpec: visSpec,
                    workflowList: visSpec.map(spec => chartToWorkflow(spec).workflow),
                },
                120_000
            );
            props.setOpen(false);
            uploadSuccess(resp?.data.dashboardId);
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
                        upload your charts to dashboard of kanaries cloud.
                    </DialogDescription>
                </DialogHeader>
                <div>
                    <div className="text-sm max-h-64 overflow-auto p-1">
                        <Label>Dashboard Name</Label>
                        <Input
                            value={chartName}
                            onChange={(e) => {
                                setChartName(e.target.value);
                            }}
                            type="text"
                            placeholder="please input chart name"
                            id="chart-name-input"
                            className="mb-1"
                        />
                        <Label>Dataset Name</Label>
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
                        <div className="flex items-center justify-end mt-2">
                            <Checkbox
                                id="link-checkbox"
                                checked={isPublic}
                                onCheckedChange={(checked) => {setIsPublic(checked as boolean);}}
                            />
                            <Label className="ml-2">Is Public?</Label>
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
