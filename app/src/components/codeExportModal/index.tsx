import React, { useEffect, useState, useCallback } from "react";
import { observer } from "mobx-react-lite";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import json from "react-syntax-highlighter/dist/esm/languages/hljs/json";
import py from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import atomOneLight from "react-syntax-highlighter/dist/esm/styles/hljs/atom-one-light";
import atomOneDark from "react-syntax-highlighter/dist/esm/styles/hljs/atom-one-dark";
import type { VizSpecStore } from "@kanaries/graphic-walker/store/visualSpecStore";
import type { IChart } from "@kanaries/graphic-walker/interfaces";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import commonStore from "@/store/common";
import { darkModeContext } from "@/store/context";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { tracker } from "@/utils/tracker";

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
    const [visSpec, setVisSpec] = useState<IChart[]>([]);
    const [tips, setTips] = useState<string>("");
    const darkMode = React.useContext(darkModeContext);

    const { pyCode } = usePythonCode({
        sourceCode,
        visSpec,
        version: commonStore.version,
    });

    const closeModal = useCallback(() => {
        setOpen(false);
    }, [setOpen]);

    const copyToCliboard = async (content: string) => {
        try {
            navigator.clipboard.writeText(content);
            setOpen(false);
        } catch(e) {
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
                <div className="text-sm max-h-64 overflow-auto p-1">
                    <Tabs defaultValue="python" className="w-full">
                        <TabsList>
                            <TabsTrigger value="python">Python</TabsTrigger>
                            <TabsTrigger value="json">JSON(Graphic Walker)</TabsTrigger>
                        </TabsList>
                        <TabsContent className="py-4" value="python">
                            <h3 className="text-sm font-medium mb-2">PyGWalker Code</h3>
                            <SyntaxHighlighter showLineNumbers language="python" style={darkMode === 'dark' ? atomOneDark : atomOneLight}>
                                {pyCode}
                            </SyntaxHighlighter>
                            <div className="text-xs max-h-56 mt-2">
                                <p>{tips}</p>
                            </div>
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
                            <SyntaxHighlighter showLineNumbers language="json" style={darkMode === 'dark' ? atomOneDark : atomOneLight}>
                                {JSON.stringify(visSpec, null, 2)}
                            </SyntaxHighlighter>
                            <div className="text-xs max-h-56 mt-2">
                                <p>{tips}</p>
                            </div>
                            <div className="mt-4 flex justify-start gap-2">
                                <Button
                                    onClick={() => {
                                        copyToCliboard(JSON.stringify(visSpec, null, 2));
                                        tracker.track("click", {"entity": "copy_code_button"});
                                    }}
                                >
                                    Copy to Clipboard
                                </Button>
                                <Button variant="outline" onClick={closeModal}>Cancel</Button>
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
            </DialogContent>
        </Dialog>
    );
});

export default CodeExport;
