import { v4 as uuidv4 } from 'uuid';
import commonStore from '../store/common';

interface IResponse {
    data?: any;
    message?: string;
    code: number;
}

interface ICommunication {
    sendMsg: (action: string, data: any, timeout?: number) => Promise<IResponse>;
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

const raiseRequestError = (message: string, code: number) => {
    let showMsg = (
        <>{message}</>
    )
    switch (code) {
        case 20001:
            showMsg = (
                <>
                <p className="py-1">kanaries_api_key is not valid.</p>
                <p className="py-1">Please set kanaries_api_key first.</p>
                <p className="py-1">If you are not kanaries user, please register it from
                    <a className="font-semibold px-1" href="https://kanaries.net/home/access" target='_blank'>
                        https://kanaries.net/home/access
                    </a>
                </p>
                <p className="py-1">Then refer
                    <a className="font-semibold px-1" href="https://github.com/Kanaries/pygwalker/wiki/How-to-get-api-key-of-kanaries%3F" target='_blank'>
                        document
                    </a>
                    to set kanaries_api_key.</p>
                </>
            );
            break;
        case 20002:
            showMsg = (<>
                <p className="py-1">
                    The usage of cloud config has reached the upper limit.
                    If you want to use more cloud config files, please subscribe to different cloud packages according to your usage:
                    <a className="font-semibold px-1" href="https://kanaries.net/home/pygwalker" target='_blank'>
                        https://kanaries.net/home/pygwalker
                    </a>
                </p>
            </>)
            break;
    }
    commonStore.setNotification({
        type: "error",
        title: "Error",
        message: showMsg || "Unknown error",
    }, 20_000);
}

const initJupyterCommunication = (gid: string) => {
    const kernelTextCount = 7;
    let curKernelTextIndex = 0;
    const jupyterEnv = getCurrentJupyterEnv();
    const document = window.parent.document;
    const htmlText = document.getElementsByClassName(`hacker-comm-pyg-html-store-${gid}`)[0].childNodes[1] as HTMLInputElement;
    const kernelTextList = Array.from({ length: kernelTextCount }, (_, index) => index).map(index => {
        return document.getElementsByClassName(`hacker-comm-pyg-kernel-store-${gid}-${index}`)[0].childNodes[1] as HTMLInputElement;
    })

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
            setTimeout(() => {
                sendMsgAsync(action, data, rid);
            }, 0);
            const timer = setTimeout(() => {
                raiseRequestError("communication timeout", 0);
                reject(new Error("get result timeout"));
            }, timeout);
            document.addEventListener(getSignalName(rid), (_) => {
                clearTimeout(timer);
                const resp = bufferMap.get(rid);
                if (resp.code !== 0) {
                    raiseRequestError(resp.message, resp.code);
                    reject(new Error(resp.message));
                }
                resolve(resp);
            });
        });

        return promise;
    }

    const sendMsgAsync = (action: string, data: any, rid: string | null) => {
        rid = rid ?? uuidv4();
        const event = new Event("input", { bubbles: true })
        const kernelText = kernelTextList[curKernelTextIndex];
        kernelText.value = JSON.stringify({ gid: gid, rid: rid, action, data });
        kernelText.dispatchEvent(event);
        curKernelTextIndex = (curKernelTextIndex + 1) % kernelTextCount;
    }

    const registerEndpoint = (action: string, callback: (data: any) => any) => {
        endpoints.set(action, callback);
    }

    if (jupyterEnv === "datalore") {
        const kernel = (window.parent as any).Jupyter.notebook.kernel;
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

const initHttpCommunication = (gid: string, baseUrl: string) => {
    // temporary solution in streamlit could
    const domain = window.parent.document.location.host.split(".").slice(-2).join('.');
    let url = "";
    if (domain === "streamlit.app") {
        url = `/~/+/_stcore/_pygwalker/comm/${gid}`
    } else {
        url = `/${baseUrl}/${gid}`
    }

    const sendMsg = async(action: string, data: any, timeout: number = 30_000) => {
        const timer = setTimeout(() => {
            raiseRequestError("communication timeout", 0);
            throw(new Error("get result timeout"));
        }, timeout);
        try {
            const resp = await (await sendMsgAsync(action, data)).json();
            if (resp.code !== 0) {
                raiseRequestError(resp.message, resp.code);
                throw new Error(resp.message);
            }
            return resp;
        } finally {
            clearTimeout(timer);
        }
    }

    const sendMsgAsync = (action: string, data: any) => {
        const rid = uuidv4();
        return fetch(
            url,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ gid, rid, action, data }),
            }
        )
    }

    const registerEndpoint = (_: string, __: (data: any) => any) => {}

    return {
        sendMsg,
        registerEndpoint,
        sendMsgAsync,
    }
}

export type { ICommunication };
export { initJupyterCommunication, initHttpCommunication };
