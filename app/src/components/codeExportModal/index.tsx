import React, { useEffect, useState, useCallback } from "react";
import { observer } from "mobx-react-lite";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import json from "react-syntax-highlighter/dist/esm/languages/hljs/json";
import py from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import atomOneLight from "react-syntax-highlighter/dist/esm/styles/hljs/atom-one-light";
import type { VizSpecStore } from '@kanaries/graphic-walker/dist/store/visualSpecStore'
import { IChartForExport } from "@kanaries/graphic-walker/dist/interfaces";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import commonStore from "@/store/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

import { usePythonCode } from "./usePythonCode";

SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("python", py);

interface ICodeExport {
    globalStore: React.MutableRefObject<VizSpecStore | null>;
    sourceCode: string;
    open: boolean;
    setOpen: (open: boolean) => void;
}

const CodeExport: React.FC<ICodeExport> = observer((props) => {
    const { globalStore, sourceCode, open, setOpen } = props;
    const [visSpec, setVisSpec] = useState<IChartForExport[]>([]);
    const [tips, setTips] = useState<string>("");

    const { pyCode } = usePythonCode({
        sourceCode,
        visSpec,
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
        if (open && globalStore.current) {
            const res = globalStore.current.exportCode();
            setVisSpec(res);
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
                                {JSON.stringify(visSpec, null, 2)}
                            </SyntaxHighlighter>
                            <div className="mt-4 flex justify-start gap-2">
                                <Button
                                    onClick={() => {
                                        copyToCliboard(JSON.stringify(visSpec, null, 2));
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
