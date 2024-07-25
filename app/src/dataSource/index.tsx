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
const DEFAULT_LIMIT = 50_000;

function notifyDataLimit() {
    commonStore.setNotification({
        type: "warning",
        title: "Data Limit Reached",
        message: (<>
            The current computation has returned more than 50,000 rows of data. 
            To ensure optimal performance, we are currently rendering only the first 50,000 rows. 
            If you need to render the entire all datas, please use the 'limit' tool 
            (<svg className="inline bg-black" width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path
                    d="M9.94969 7.49989C9.94969 8.85288 8.85288 9.94969 7.49989 9.94969C6.14691 9.94969 5.0501 8.85288 5.0501 7.49989C5.0501 6.14691 6.14691 5.0501 7.49989 5.0501C8.85288 5.0501 9.94969 6.14691 9.94969 7.49989ZM10.8632 8C10.6213 9.64055 9.20764 10.8997 7.49989 10.8997C5.79214 10.8997 4.37847 9.64055 4.13662 8H0.5C0.223858 8 0 7.77614 0 7.5C0 7.22386 0.223858 7 0.5 7H4.13659C4.37835 5.35935 5.79206 4.1001 7.49989 4.1001C9.20772 4.1001 10.6214 5.35935 10.8632 7H14.5C14.7761 7 15 7.22386 15 7.5C15 7.77614 14.7761 8 14.5 8H10.8632Z"
                    fill="currentColor"
                    fillRule="evenodd"
                    clipRule="evenodd"
                ></path>
            </svg>) to manually set the maximum number of rows to be returned.
        </>)
    }, 60_000);
}

export function getDatasFromKernelBySql(fieldMetas: any) {
    return async (payload: IDataQueryPayload) => {
        const sql = parser_dsl_with_meta(
            "pygwalker_mid_table",
            JSON.stringify({...payload, limit: payload.limit ?? DEFAULT_LIMIT}),
            JSON.stringify({"pygwalker_mid_table": fieldMetas})
        );
        const result = await batchGetDatasBySql.getDatas(sql) ?? [];
        if (!payload.limit && result.length === DEFAULT_LIMIT) {
            notifyDataLimit();
        }
        return result as IRow[];
    }
}

export async function getDatasFromKernelByPayload(payload: IDataQueryPayload) {
    const result = await batchGetDatasByPayload.getDatas({...payload, limit: payload.limit ?? DEFAULT_LIMIT}) ?? [];
    if (!payload.limit && result.length === DEFAULT_LIMIT) {
        notifyDataLimit();
    }
    return result as IRow[];
}
