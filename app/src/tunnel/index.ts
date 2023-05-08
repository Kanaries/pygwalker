import { getNewComm } from "../utils/comm";

export class Tunnel {
    private _opened_promise: Promise<boolean>;
    private _message_handlers: Array<(msg: any, ...props: any[]) => any> = [];
    private _close_handlers: Array<(reason?: any) => any> = [];
    private _unhandled: Array<[any, Array<any>]> = [];
    private comm: any;
    private _on_message = async (msg: any, ...props: any[]) => {
        // if (process.env.NODE_ENV === 'develop') {
        //     console.log("tunnel message:", msg);
        //     console.log("attached message:", props);
        // }
        await this._opened_promise;
        if (this._message_handlers) await Promise.all(this._message_handlers.map(handler => handler(msg, ...props)));
        else {
            this._unhandled.push([msg, props]);
        }
    }
    private _on_close = async (reason: any) => {
        await Promise.all(this._close_handlers.map(handler => handler(reason)));
    }
    private async _open (tunnelId: string, window: Window) {
        let comm = getNewComm(window, tunnelId, this._on_message, this._on_close);
        try {
            this.comm = await comm;
        } catch(err) {
            console.log("comm:", err);
        }
    }

    constructor(tunnelId: string, _window: Window = window) {
        this._opened_promise = new Promise((resolve, reject) => {
            this._open(tunnelId, _window).then(() => {
                resolve(true);
            }).catch(err => {
                reject(err);
            });
        });
    }
    public get opened(): Promise<boolean> {
        return this._opened_promise;
    }
    public async send(msg: any) {
        await this._opened_promise;
        const promises = new Array<any>();
        if (this.comm) {
            promises.push(this.comm.send(msg));
        }
        return Promise.all(promises);
    }
    public onMessage(handler: (msg: any, ...props: any[]) => any) {
        this._message_handlers.push(handler);
        if (this._unhandled.length) {
            for (let [msg, props] of this._unhandled) {
                handler(msg, ...props);
            }
        }
    }
    public onClose(handler: (reason?: any) => any) {
        this._close_handlers.push(handler);
    }
    public close() {
        if (this.comm) this.comm.close();
    }
}