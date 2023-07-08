import { v4 as uuidv4 } from 'uuid';

interface ICommunication {
    sendMsg: (action: string, data: any, timeout?: number) => Promise<any>;
    registerEndpoint: (action: string, callback: (data: any) => any) => void;
    sendMsgAsync: (action: string, data: any, rid: string | null) => void;
}

const getSignalName = (rid: string) => {
    return `hacker-comm-pyg-done-signal-${rid}`;
}

const getCurrentJupyterEnv = () => {
    const host = window.parent.location.host;
    if (host === 'datalore.jetbrains.com') {
        return 'datalore';
    }
    return "jupyter";
}

const initCommunication = (gid: string) => {
    const jupyterEnv = getCurrentJupyterEnv();
    const document = window.parent.document;
    const htmlText = document.getElementsByClassName(`hacker-comm-pyg-html-store-${gid}`)[0].childNodes[1] as HTMLInputElement;
    const kernelText = document.getElementsByClassName(`hacker-comm-pyg-kernel-store-${gid}`)[0].childNodes[1] as HTMLInputElement;;

    const endpoints = new Map<string, (data: any) => any>();
    const bufferMap = new Map<string, any>();

    const onMessage = (msg: string) => {
        const data = JSON.parse(msg);
        const action = data.action;
        if (action === "finish_request") {
            bufferMap.set(data.rid, data.data);
            document.dispatchEvent(new CustomEvent(getSignalName(data.rid)));
            return
        }
        const callback = endpoints.get(action);
        if (callback) {
            const resp = callback(data.data) ?? {};
            sendMsgAsync("finish_request", resp, data.rid);
        }
    }

    const sendMsg = async(action: string, data: any, timeout: number = 30_000) => {
        const rid = uuidv4();
        const promise = new Promise<any>((resolve, reject) => {
            sendMsgAsync(action, data, rid);
            setTimeout(() => {
                reject(new Error("get result timeout"))
            }, timeout);
            document.addEventListener(getSignalName(rid), (_) => {
                resolve(bufferMap.get(rid));
            });
        });

        return promise;
    }

    const sendMsgAsync = (action: string, data: any, rid: string | null) => {
        rid = rid ?? uuidv4();
        const event = new Event("input", { bubbles: true })
        kernelText.value = JSON.stringify({ gid: gid, rid: rid, action, data });
        kernelText.dispatchEvent(event);
    }

    const registerEndpoint = (action: string, callback: (data: any) => any) => {
        endpoints.set(action, callback);
    }

    if (jupyterEnv === "datalore") {
        const kernel = window.parent.Jupyter.notebook.kernel;
        if (kernel.__pre_can_handle_message === undefined) {
            kernel.__pre_can_handle_message = kernel._can_handle_message;
        }
        kernel._can_handle_message = (msg: any) => {
            if (msg.msg_type === "comm_msg" && msg.content.data.method === "update") {
                const pygMsgStr = msg.content.data.state.value;
                try {
                    if (JSON.parse(pygMsgStr).gid === gid) {
                        onMessage(pygMsgStr);
                    }
                } catch (_) {}
            }
            return kernel.__pre_can_handle_message(msg);
        }
    } else {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === "attributes") {
                    onMessage(htmlText.value)
                }
            })
        })
        observer.observe(htmlText, {
            attributes: true,
            attributeFilter: ["placeholder"],
        })
    }

    return {
        sendMsg,
        registerEndpoint,
        sendMsgAsync,
    }
}

export type { ICommunication };
export default initCommunication;
