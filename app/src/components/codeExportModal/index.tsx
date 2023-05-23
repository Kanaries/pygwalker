import React, { useEffect, useState, useMemo } from "react";
import Modal from "../modal";
import { observer } from "mobx-react-lite";
import DefaultButton from "../button/default";
import PrimaryButton from "../button/primary";
import SavePygConfigButton from './saveConfigButton';

const syntaxHighlight = (json: any) => {
    if (typeof json != "string") {
        json = JSON.stringify(json, undefined, 4);
    }
    json = json
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>")
        .replace(/\t/g, "&nbsp;&nbsp;&nbsp;&nbsp;")
        .replace(/\s/g, "&nbsp;");
    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            var cls = "text-sky-500"; // number
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = "text-purple-500"; // key
                } else {
                    cls = "text-emerald-500"; // string
                }
            } else if (/true|false/.test(match)) {
                cls = "text-blue-500";
            } else if (/null/.test(match)) {
                cls = "text-sky-500";
            }
            return '<span class="' + cls + '">' + match + "</span>";
        }
    );
};

interface ICodeExport {
    globalStore: any;
    sourceCode: string;
    open: boolean;
    setOpen: (open: boolean) => void;
}

const CodeExport: React.FC<ICodeExport> = observer((props) => {
    const [code, setCode] = useState<any>("");
    const [pygCode, setPygCode] = useState<string>("");
    const [tips, setTips] = useState<string>("");

    const copyOutput = useMemo(() => {
        let output = JSON.stringify(code);
        return output;
    }, [code]);

    useEffect(() => {
        if (props.open) {
            const res = props.globalStore?.current?.vizStore?.exportViewSpec();
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
                <div className="text-sm px-6 max-h-64 overflow-auto">
                    <code dangerouslySetInnerHTML={{ __html: syntaxHighlight(code) }} />
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
                        text="Cancal"
                        className="mr-2 px-6"
                        onClick={() => {
                            props.setOpen(false);
                        }}
                    />
                </div>
                <div className="text-sm px-6 max-h-56 mt-4">
                    <textarea style={{fontFamily: "monospace"}} readOnly={true} rows={3} cols={90} wrap="off" defaultValue={pygCode} />
                    <p style={{textAlign: 'right'}}>{tips}</p>
                </div>
            </div>
        </Modal>
    );
});

export default CodeExport;
