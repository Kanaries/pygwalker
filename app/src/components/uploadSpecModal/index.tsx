import React, { useState } from "react";
import { observer } from "mobx-react-lite";

import communicationStore from "../../store/communication";
import commonStore from "../../store/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface IUploadSpecModal {
}

const UploadSpecModal: React.FC<IUploadSpecModal> = observer((props) => {
    const [uploading, setUploading] = useState(false);
    const [specName, setSpecName] = useState("");
    const [isSetToken, setIsSetToken] = useState(false);
    const [token, setToken] = useState("");

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
        setUploading(true);

        try {

            const resp = await communicationStore.comm?.sendMsg(
                "upload_spec_to_cloud",
                {"fileName": specName, "newToken": isSetToken ? token : ""},
                30_000
            );
            commonStore.setUploadSpecModalOpen(false);
            uploadSuccess(resp?.data["specFilePath"]);
        } finally {
            setUploading(false);
        }
    };

    const onClickSetToken = (checked: boolean) => {
        setIsSetToken(checked);
        setToken("");
    }

    return (
        <Dialog
            open={commonStore.uploadSpecModalOpen}
            modal={false}
            onOpenChange={(show) => {
                commonStore.setUploadSpecModalOpen(show);
            }}
        >
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Upload Sepc</DialogTitle>
                    <DialogDescription>
                    <p className="py-1">Because you currently don't pass in the spec parameter or the passed in spec parameter is not a writable spec file.</p>
                    <p className="py-1">Currently the spec configuration is already in your ui cache, you may need to upload kanaries cloud to save it.</p>
                    <p className="py-1">If you don't have kanaries_token, you need to get it first, refer to: <a className="font-semibold px-1" href="https://github.com/Kanaries/pygwalker/wiki/How-to-get-api-key-of-kanaries%3F" target="_blank">How to get api key of kanaries?</a></p>
                    </DialogDescription>
                </DialogHeader>
                <div>
                    <div className="text-sm max-h-64 overflow-auto">
                        <input
                            value={specName}
                            onChange={(e) => {
                                setSpecName(e.target.value);
                            }}
                            type="text"
                            placeholder="please input spec file name"
                            id="chart-name-input"
                            className="block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                        />
                    </div>
                    <div className="flex items-center justify-end mt-2">
                        <input
                            id="link-checkbox"
                            type="checkbox"
                            checked={isSetToken}
                            onChange={(e) => {
                                onClickSetToken(e.target.checked);
                            }}
                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                        />
                        <label className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-300">Set a new kanaries_token?</label>
                    </div>
                    {
                        isSetToken && (
                            <div className="text-sm max-h-64 overflow-auto mt-2">
                                <input
                                    value={token}
                                    onChange={(e) => {
                                        setToken(e.target.value);
                                    }}
                                    type="text"
                                    autoComplete="off"
                                    placeholder="please input new kanaries token"
                                    id="token-input"
                                    className="block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
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
        </Dialog>
    );
});

export default UploadSpecModal;
