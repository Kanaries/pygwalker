import React, { useEffect, useState, useMemo } from "react";
import Modal from "../modal";
import { observer } from "mobx-react-lite";
import DefaultButton from "../button/default";
import PrimaryButton from "../button/primary";
import SavePygConfigButton from './saveConfigButton';
import { encodeSpec } from "../../utils/graphicWalkerParser"

import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import py from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import atomOneLight from 'react-syntax-highlighter/dist/esm/styles/hljs/atom-one-light';

import type { IGlobalStore } from '@kanaries/graphic-walker/dist/store'
import type { IVisSpec } from '@kanaries/graphic-walker/dist/interfaces'

SyntaxHighlighter.registerLanguage('json', json);
SyntaxHighlighter.registerLanguage('python', py);

interface ICodeExport {
    globalStore: React.MutableRefObject<IGlobalStore | null>;
    sourceCode: string;
    open: boolean;
    setOpen: (open: boolean) => void;
}

const CodeExport: React.FC<ICodeExport> = observer((props) => {
    const [code, setCode] = useState<IVisSpec[]>([]);
    const [pygCode, setPygCode] = useState<string>("");
    const [tips, setTips] = useState<string>("");

    useEffect(() => {
        if (props.open) {
            const res = props.globalStore.current?.vizStore.exportViewSpec()!;
            setCode(res);
        }
    }, [props.open]);

    return (
        <Modal
            show={props.open}
            onClose={() => {
                props.setOpen(false);
            }}
        >
            <div>
                <h1 className="mb-4">Code Export</h1>
                <div className="text-sm max-h-64 overflow-auto">
                    <h2 className="text-sm mb-2">graphic walker spec</h2>
                    <SyntaxHighlighter showLineNumbers language="json" style={atomOneLight}>
                        { JSON.stringify(JSON.parse(encodeSpec(code)), null, 2) }
                    </SyntaxHighlighter>
                </div>
                <div className="mt-4 flex justify-start">
                    <PrimaryButton
                        className="mr-2 px-6"
                        text="Copy to Clipboard"
                        onClick={async () => {
                            const queryOpts = { name: 'clipboard-read' as PermissionName, allowWithoutGesture: false };
                            const permissionStatus = await navigator.permissions.query(queryOpts);
                            try {
                                if (permissionStatus.state !== 'denied') {
                                    navigator.clipboard.writeText(pygCode);
                                    props.setOpen(false);
                                }
                                else { setTips("The Clipboard API has been blocked in this environment. Please copy manully."); }
                            } catch(e) { setTips("The Clipboard API has been blocked in this environment. Please copy manully."); }
                        }}
                    />
                    <SavePygConfigButton
                        sourceCode={props.sourceCode}
                        configJson={code}
                        setPygCode={setPygCode}
                        setTips={setTips}
                    />
                    <DefaultButton
                        text="Cancel"
                        className="mr-2 px-6"
                        onClick={() => {
                            props.setOpen(false);
                        }}
                    />
                </div>
                <div className="text-sm max-h-56 mt-4">
                    <SyntaxHighlighter showLineNumbers language="python" style={atomOneLight}>
                        {pygCode}
                    </SyntaxHighlighter>
                    <p style={{textAlign: 'right'}}>{tips}</p>
                </div>
            </div>
        </Modal>
    );
});

export default CodeExport;
