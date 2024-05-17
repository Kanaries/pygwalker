import React, { useEffect, useState } from "react";
import { observer } from "mobx-react-lite";
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore'
import { chartToWorkflow } from "@kanaries/graphic-walker/utils/workflow";
import { tracker } from "@/utils/tracker";

import communicationStore from "../../store/communication";
import commonStore from "../../store/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { badgeVariants } from "@/components/ui/badge";

interface IUploadSpecModal {
    setGwIsChanged: React.Dispatch<React.SetStateAction<boolean>>;
    storeRef: React.MutableRefObject<VizSpecStore | null>;
}

const UploadSpecModal: React.FC<IUploadSpecModal> = observer((props) => {
    const [uploading, setUploading] = useState(false);
    const [specName, setSpecName] = useState("");
    const [isSetToken, setIsSetToken] = useState(false);
    const [token, setToken] = useState("");
    const [contentType, setContentType] = useState<"onboarding" | "upload">("onboarding");

    const uploadSuccess = (path: string) => {
        commonStore.setNotification(
            {
                type: "success",
                title: "Success",
                message: (
                    <>
                    <p className="py-1">upload spec success, please use</p>
                    <p className="font-semibold px-1 py-1">`pyg.walk(df, spec="ksf://{path}")`</p>
                    <p className="py-1">to rerun pygwalker.</p>
                    </>
                ),
            },
            30_000
        );
    };

    const onClick = async () => {
        if (uploading) return;
        tracker.track("click", {"entity": "upload_spec_to_cloud_button"});
        setUploading(true);

        try {

            const resp = await communicationStore.comm?.sendMsg(
                "upload_spec_to_cloud",
                {"fileName": specName, "newToken": isSetToken ? token : ""},
                30_000
            );
            commonStore.setUploadSpecModalOpen(false);
            uploadSuccess(resp?.data["specFilePath"]);
            props.setGwIsChanged(false);
        } finally {
            setUploading(false);
        }
    };

    const onClickSetToken = (checked: boolean) => {
        setIsSetToken(checked);
        setToken("");
    }

    const saveSpecToLocal = () => {
        tracker.track("click", {"entity": "save_spec_to_local_file_button"});
        const visSpec = props.storeRef.current?.exportCode();
        const configObj = {
            config: visSpec,
            chart_map: {},
            version: commonStore.version,
            workflow_list: visSpec?.map(spec => chartToWorkflow(spec).workflow),
        }
        const blob = new Blob([JSON.stringify(configObj)], {type: "text/plain;charset=utf-8"});
        const url = URL.createObjectURL(blob);
        const tempLink = document.createElement("a");
        tempLink.href = url;
        tempLink.download = `pygwalker_spec_${new Date().getTime()}.json`
        tempLink.click();
        URL.revokeObjectURL(url);
        commonStore.setUploadSpecModalOpen(false);
        props.setGwIsChanged(false);
    };

    useEffect(() => {
        setContentType("onboarding");
    }, [commonStore.uploadSpecModalOpen]);

    const OnboardingContent = (
        <DialogContent>
            <DialogHeader>
                <DialogTitle>Save Spec</DialogTitle>
            </DialogHeader>
            <div className="grid h-full grid-rows-2 gap-6 lg:grid-cols-2 lg:grid-rows-1">
                <button
                    className={"flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent"}
                    onClick={() => {
                        setContentType("upload");
                        tracker.track("click", {"entity": "select_upload_spec_to_cloud_button"});
                    }}
                >
                    <div className="flex items-center justify-center h-[160px] w-full">
                        <span className="font-semibold">upload as cloud file</span>
                    </div>
                </button>
                <button
                    className={"flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent"}
                    onClick={saveSpecToLocal}
                >
                    <div className="flex items-center justify-center h-[160px] w-full">
                        <span className="font-semibold">save as local file</span>
                    </div>
                </button>
            </div>
        </DialogContent>
    )

    const UpdateSpecContent = (
        <DialogContent>
            <DialogHeader>
                <DialogTitle>Upload Sepc</DialogTitle>
                <DialogDescription>
                <p className="py-1">Because you currently don't pass in the spec parameter or the passed in spec parameter is not a writable spec file.</p>
                <p className="py-1">Currently the spec configuration is already in your ui cache, you may need to upload kanaries cloud to save it.</p>
                <p className="py-1">If you don't have kanaries_token, you need to get it: <a className={badgeVariants({ variant: "outline" })} href="https://kanaries.net/analytics/settings?tab=apikey" target="_blank">Kanaries</a></p>
                </DialogDescription>
            </DialogHeader>
            <div>
                <div className="text-sm max-h-64 overflow-auto p-1">
                    <Input
                        value={specName}
                        onChange={(e) => {
                            setSpecName(e.target.value);
                        }}
                        type="text"
                        placeholder="please input spec file name"
                        id="chart-name-input"
                        className="mb-1"
                    />
                </div>
                <div className="flex items-center justify-end mt-2">
                    <Checkbox
                        id="link-checkbox"
                        checked={isSetToken}
                        onCheckedChange={(checked) => {
                            onClickSetToken(checked as boolean);
                        }}
                    />
                    <Label className="ml-2">Set a new kanaries_token?</Label>
                </div>
                {
                    isSetToken && (
                        <div className="text-sm max-h-64 overflow-auto p-1 mt-2">
                            <Input
                                value={token}
                                onChange={(e) => {
                                    setToken(e.target.value);
                                }}
                                type="text"
                                autoComplete="off"
                                placeholder="please input new kanaries token"
                                id="token-input"
                            />
                        </div>
                    )
                }
                <div className="mt-4 flex justify-end">
                    <Button variant="outline" className="mr-2 px-6" disabled={uploading} onClick={onClick}>
                        {uploading ? "uploading.." : "upload"}
                    </Button>
                </div>
            </div>
        </DialogContent>
    )

    return (
        <Dialog
            open={commonStore.uploadSpecModalOpen}
            modal={false}
            onOpenChange={(show) => {
                commonStore.setUploadSpecModalOpen(show);
            }}
        >
            {contentType === "upload" && UpdateSpecContent }
            {contentType === "onboarding" && OnboardingContent }
        </Dialog>
    );
});

export default UploadSpecModal;
