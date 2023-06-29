import type { IDataSourceProps } from "../interfaces";
import type { IRow } from "@kanaries/graphic-walker/dist/interfaces";

interface MessagePayload extends IDataSourceProps {
    action: "requestData" | "postData" | "finishData";
    tunnelId: string;
    dataSourceId: string;
    partId: number;
    data?: IRow[];
}
export async function loadDataSource(props: IDataSourceProps): Promise<IRow[]> {
    const { tunnelId, dataSourceId } = props;

    return new Promise((resolve, reject) => {
        let partId = 0;
        window.postMessage(
            {
                action: "requestData",
                tunnelId: tunnelId,
                dataSourceId: dataSourceId,
                partId,
            } as MessagePayload,
            "*"
        );
        const data = new Array<IRow>();
        const timeout = () => {
            reject("timeout");
        };
        let timer = setTimeout(timeout, 100_000);
        const onmessage = (ev: MessageEvent<MessagePayload>) => {
            try {
                if (ev.data.tunnelId === tunnelId && ev.data.dataSourceId === dataSourceId) {
                    clearTimeout(timer);
                    timer = setTimeout(timeout, 100_000);
                    if (ev.data.action === "postData") {
                        partId += 1;
                        window.postMessage(
                            {
                                action: "requestData",
                                tunnelId: tunnelId,
                                dataSourceId: dataSourceId,
                                partId,
                            },
                            "*"
                        );
                        data.push(...(ev.data.data ?? []));
                    } else if (ev.data.action === "finishData") {
                        window.removeEventListener("message", onmessage);
                        resolve(data);
                    }
                }
            } catch (err) {
                console.error(err);
                reject({ message: "handler", error: err });
            }
        };
        window.addEventListener("message", onmessage);
    });
}
