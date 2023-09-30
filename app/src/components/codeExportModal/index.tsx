import React, { useEffect, useState, useCallback } from "react";
import { observer } from "mobx-react-lite";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import json from "react-syntax-highlighter/dist/esm/languages/hljs/json";
import py from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import atomOneLight from "react-syntax-highlighter/dist/esm/styles/hljs/atom-one-light";
import type { IGlobalStore } from "@kanaries/graphic-walker/dist/store";
import type { IVisSpec } from "@kanaries/graphic-walker/dist/interfaces";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import commonStore from "@/store/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

import { usePythonCode } from "./usePythonCode";

SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("python", py);

interface ICodeExport {
    globalStore: React.MutableRefObject<IGlobalStore | null>;
    sourceCode: string;
    open: boolean;
    setOpen: (open: boolean) => void;
}

const CodeExport: React.FC<ICodeExport> = observer((props) => {
    const { globalStore, sourceCode, open, setOpen } = props;
    const [specList, setSpecList] = useState<IVisSpec[]>([]);
    const [tips, setTips] = useState<string>("");

    const { pyCode } = usePythonCode({
        sourceCode,
        specList,
        version: commonStore.version,
    });

    const closeModal = useCallback(() => {
        setOpen(false);
    }, [setOpen]);

    const copyToCliboard = async (content: string) => {
        const queryOpts = { name: "clipboard-read" as PermissionName, allowWithoutGesture: false };
        const permissionStatus = await navigator.permissions.query(queryOpts);
        try {
            if (permissionStatus.state !== "denied") {
                navigator.clipboard.writeText(content);
                setOpen(false);
            } else {
                setTips("The Clipboard API has been blocked in this environment. Please copy manully.");
            }
        } catch (e) {
            setTips("The Clipboard API has been blocked in this environment. Please copy manully.");
        }
    };

    useEffect(() => {
        if (open) {
            const res = globalStore.current?.vizStore.exportViewSpec()! as IVisSpec[];
            setSpecList(res);
        }
    }, [open]);

    return (
        <Dialog
            open={open}
            modal={false}
            onOpenChange={(show) => {
                setOpen(show);
            }}
        >
            <DialogContent className="sm:max-w-[90%] lg:max-w-[900px]">
                <DialogHeader>
                    <DialogTitle>Code Export</DialogTitle>
                    <DialogDescription>
                        Export the code of all charts in PyGWalker.
                    </DialogDescription>
                </DialogHeader>
                <div className="text-sm max-h-64 overflow-auto">
                    <Tabs defaultValue="python" className="w-full">
                        <TabsList>
                            <TabsTrigger value="python">Python</TabsTrigger>
                            <TabsTrigger value="json">JSON(Graphic Walker)</TabsTrigger>
                        </TabsList>
                        <div className="text-xs max-h-56 mt-2">
                            <p>{tips}</p>
                        </div>
                        <TabsContent className="py-4" value="python">
                            <h3 className="text-sm font-medium mb-2">PyGWalker Code</h3>
                            <SyntaxHighlighter showLineNumbers language="python" style={atomOneLight}>
                                {pyCode}
                            </SyntaxHighlighter>
                            <div className="mt-4 flex justify-start gap-2">
                                <Button
                                    onClick={() => {
                                        copyToCliboard(pyCode);
                                    }}
                                >
                                    Copy to Clipboard
                                </Button>
                                <Button variant="outline" onClick={closeModal}>
                                    Cancel
                                </Button>
                            </div>
                        </TabsContent>
                        <TabsContent value="json">
                            <h3 className="text-sm font-medium mb-2">Graphic Walker Specification</h3>
                            <SyntaxHighlighter showLineNumbers language="json" style={atomOneLight}>
                                {JSON.stringify(specList, null, 2)}
                            </SyntaxHighlighter>
                            <div className="mt-4 flex justify-start gap-2">
                                <Button
                                    onClick={() => {
                                        copyToCliboard(JSON.stringify(specList, null, 2));
                                    }}
                                >
                                    Copy to Clipboard
                                </Button>
                                <Button variant="outline">Cancel</Button>
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
            </DialogContent>
        </Dialog>
    );
});

export default CodeExport;
