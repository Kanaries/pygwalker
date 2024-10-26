import { v4 as uuidv4 } from 'uuid';
import commonStore from '../store/common';
import { Streamlit } from "streamlit-component-lib"

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
                <p className="py-1">execute it in terminal:</p>
                <p className="font-semibold px-1 py-1">`pygwalker login`</p>
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
    const kernelTextCount = 5;
    let curKernelTextIndex = 0;
    const jupyterEnv = getCurrentJupyterEnv();
    const document = window.parent.document;
    const htmlText = document.getElementsByClassName(`hacker-comm-pyg-html-store-${gid}`)[0].childNodes[1] as HTMLInputElement;
    const kernelTextList = Array.from({ length: kernelTextCount }, (_, index) => index).map(index => {
        return document.getElementsByClassName(`hacker-comm-pyg-kernel-store-${gid}-${index}`)[0].childNodes[1] as HTMLInputElement;
    })

    const endpoints = new Map<string, (data: any) => any>();
    const bufferMap = new Map<string, any>();

    const fetchOnJupyter = (value: string) => {
        const event = new Event("input", { bubbles: true })
        const kernelText = kernelTextList[curKernelTextIndex];
        kernelText.value = value;
        kernelText.dispatchEvent(event);
        curKernelTextIndex = (curKernelTextIndex + 1) % kernelTextCount;
    }

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
        fetchOnJupyter(JSON.stringify({ gid, rid, action, data }));
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

const getRealApiUrl = async(basePath: string, baseApiUrl: string) => {
    if (basePath === "") {
        return baseApiUrl;
    }

    const basePathPart = basePath.split("/");
    const possibleBasePaths: string[] = [];
    for (let i = basePathPart.length; i >= 0; i--) {
        possibleBasePaths.push(basePathPart.slice(0, i).join("/"));
    }
    const possibleApiUrls = possibleBasePaths.slice(0, 2).map(path => `${path.length === 0 ? '' : '/'}${path}/${baseApiUrl}`);

    return (await Promise.all(possibleApiUrls.map(async(url) => {
        try {
            const resp = await fetch(
                url,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ action: "ping", data: {} }),
                }
            )
            const respJson = await resp.json();
            if (respJson.code === 0) {
                return url;
            }
            return null;
        } catch {
            return null;
        }
    }))).find(url => url !== null) as string;
}

const initHttpCommunication = async(gid: string, baseUrl: string) => {
    // temporary solution in streamlit could
    const domain = window.parent.document.location.host.split(".").slice(-2).join('.');
    let url = "";
    if (domain === "streamlit.app") {
        url = `/~/+/_stcore/_pygwalker/comm/${gid}`
    } else {
        const basePath = window.parent.location.pathname.replace(/\/+$/, '').replace(/^\/+/, '');
        url = await getRealApiUrl(basePath, `${baseUrl}/${gid}`);
    }
   url = "/" + url.replace(new RegExp(`/*`), "");

    const sendMsg = async(action: string, data: any, timeout: number = 30_000) => {
        const timer = setTimeout(() => {
            raiseRequestError("communication timeout", 0);
            throw(new Error("get result timeout"));
        }, timeout);
        try {
            const resp = await sendMsgAsync(action, data);
            if (resp.code !== 0) {
                raiseRequestError(resp.message, resp.code);
                throw new Error(resp.message);
            }
            return resp;
        } finally {
            clearTimeout(timer);
        }
    }

    const sendMsgAsync = async(action: string, data: any) => {
        const rid = uuidv4();
        return await (await fetch(
            url,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action, data, rid, gid }),
            }
        )).json();
    }

    const registerEndpoint = (_: string, __: (data: any) => any) => {}

    return {
        sendMsg,
        registerEndpoint,
        sendMsgAsync,
    }
}

const streamlitComponentCallback = (data: any) => {
    if (commonStore.isStreamlitComponent) {
        Streamlit.setComponentValue(data);
    }
}

const initAnywidgetCommunication = async(gid: string, model: import("@anywidget/types").AnyModel) => {
    const bufferMap = new Map<string, any>();

    const onMessage = (msg: string) => {
        const data = JSON.parse(msg);
        const action = data.action;
        if (action === "finish_request") {
            bufferMap.set(data.rid, data.data);
            document.dispatchEvent(new CustomEvent(getSignalName(data.rid)));
            return
        }
    }

    model.on("msg:custom", msg => {
        if (msg.type !== "pyg_response") {
            return;
        }
        onMessage(msg.data);
    });

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
        model.send({type: "pyg_request", msg: { gid, rid, action, data }});
    }

    const registerEndpoint = (_: string, __: (data: any) => any) => {}

    return {
        sendMsg,
        registerEndpoint,
        sendMsgAsync,
    }
}

export type { ICommunication };
export { initJupyterCommunication, initHttpCommunication, streamlitComponentCallback, initAnywidgetCommunication };
