type AnyWindow = Window & { [k: string]: any };

export async function getNewComm (
    window: AnyWindow,
    tunnelId: string, // == targetName
    onMsg: (msg: any, ...props: any[]) => any,
    onClose?: (msg: any, ...props: any[]) => any) {
    // Colab:
    return new Promise(async (resolve, reject) => {
        let retryCount = 0;
        const retryMax = -1;
        const retryInterval = 5000;
        let retryTimer;
        const retry = async () => {
            if (retryMax > 0 && retryCount++ > retryMax) {
                clearInterval(retryTimer);
                reject("getNewComm: max retry count reached");
            }
            if (window.jupyterlab) { // jupyterlab/kaggle 
                const kernel = window.jupyterlab.shell?.currentWidget?.sessionContext?.session?.kernel;
                const comm = kernel?.createComm(tunnelId);
                const on_msg = (msg: any) => {
                    if (onMsg) onMsg(msg.content.data, msg);
                }
                // Notes: If the handler returns a promise, all kernel message processing pauses until the promise is resolved.
                if (comm) {
                    comm.onMsg = on_msg;
                    if (onClose) comm.onClose = onClose;
                    await comm.open({'action': 'open'}).done;
                    clearInterval(retryTimer);
                    resolve(comm);
                }
            } else if (window.Jupyter?.notebook) {
                const kernel = window.Jupyter.notebook.kernel;
                const comm = kernel?.comm_manager?.new_comm(tunnelId, {'action': 'open'});
                const on_msg = (msg: any) => {
                    if (onMsg) onMsg(msg.content.data, msg);
                }
                if (comm) {
                    comm.on_msg(on_msg);
                    if (onClose) comm.on_close(onClose);
                    clearInterval(retryTimer);
                    resolve(comm);
                }
            } else {
                console.error("getNewComm: no comm found", window);
            }
        };
        retryTimer = setInterval(retry, retryInterval);
    });
}
