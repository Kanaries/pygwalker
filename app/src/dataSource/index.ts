import type { IDataSourceProps } from "../interfaces";
import type { IRow, IDataQueryPayload } from "@kanaries/graphic-walker/interfaces";
import commonStore from "../store/common";
import communicationStore from "../store/communication"
import { parser_dsl_with_meta } from "@kanaries/gw-dsl-parser";

interface MessagePayload extends IDataSourceProps {
    action: "requestData" | "postData" | "finishData";
    dataSourceId: string;
    partId: number;
    curIndex: number;
    total: number;
    data?: IRow[];
}

interface ICommPostDataMessage {
    dataSourceId: string;
    data?: IRow[];
    total: number;
    curIndex: number;
}

export async function loadDataSource(props: IDataSourceProps): Promise<IRow[]> {
    const { dataSourceId } = props;

    return new Promise((resolve, reject) => {
        const data = new Array<IRow>();
        const timeout = () => {
            reject("timeout");
        };
        let timer = setTimeout(timeout, 100_000);
        const onmessage = (ev: MessageEvent<MessagePayload>) => {
            try {
                if (ev.data.dataSourceId === dataSourceId) {
                    clearTimeout(timer);
                    timer = setTimeout(timeout, 100_000);
                    if (ev.data.action === "postData") {
                        commonStore.setInitModalOpen(true);
                        commonStore.setInitModalInfo({
                            total: ev.data.total,
                            curIndex: ev.data.curIndex,
                            title: "Loading Data",
                        });
                        data.push(...(ev.data.data ?? []));
                    } else if (ev.data.action === "finishData") {
                        window.removeEventListener("message", onmessage);
                        resolve(data);
                    }
                }
            } catch (err) {
                reject({ message: "handler", error: err });
            }
        };
        window.addEventListener("message", onmessage);
    });
}

export function postDataService(msg: ICommPostDataMessage) {
    window.postMessage(
        {
            action: "postData",
            dataSourceId: msg.dataSourceId,
            total: msg.total,
            curIndex: msg.curIndex,
            data: msg.data,
        } as MessagePayload,
        "*"
    )
}

export function finishDataService(msg: any) {
    window.postMessage(
        {
            action: "finishData",
            dataSourceId: msg.dataSourceId,
        } as MessagePayload,
        "*"
    )
}

interface IBatchGetDatasTask {
    query: any;
    resolve: (value: any) => void;
    reject: (reason?: any) => void;
}

function initBatchGetDatas(action: string) {
    const taskList = [] as IBatchGetDatasTask[];

    const batchGetDatas = async(taskList: IBatchGetDatasTask[]) => {
        const result = await communicationStore.comm?.sendMsg(
            action,
            {"queryList": taskList.map(task => task.query)},
            60_000
        );
        if (result) {
            for (let i = 0; i < taskList.length; i++) {
                taskList[i].resolve(result["data"]["datas"][i]);
            }
        } else {
            for (let i = 0; i < taskList.length; i++) {
                taskList[i].reject("get result error");
            }
        }
    }

    const getDatas = (query: any) => {
        return new Promise<any>((resolve, reject) => {
            taskList.push({ query, resolve, reject });
            if (taskList.length === 1) {
                setTimeout(() => {
                    batchGetDatas(taskList.splice(0, taskList.length));
                }, 100);
            }
        })
    }

    return {
        getDatas
    }
}

const batchGetDatasBySql = initBatchGetDatas("batch_get_datas_by_sql");
const batchGetDatasByPayload = initBatchGetDatas("batch_get_datas_by_payload");

export function getDatasFromKernelBySql(fieldMetas: any) {
    return async (payload: IDataQueryPayload) => {
        const sql = parser_dsl_with_meta(
            "pygwalker_mid_table",
            JSON.stringify(payload),
            JSON.stringify({"pygwalker_mid_table": fieldMetas})
        );
        const result = await batchGetDatasBySql.getDatas(sql);
        return (result ?? []) as IRow[];
    }
}

export async function getDatasFromKernelByPayload(payload: IDataQueryPayload) {
    const result = await batchGetDatasByPayload.getDatas(payload);
    return (result ?? []) as IRow[];
}
