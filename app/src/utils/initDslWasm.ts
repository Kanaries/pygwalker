import "./wasm_exec.js";
import pako from "pako";
import { Buffer } from 'buffer';

declare global {
    export interface Window {
        Go: any;
    }
}

export async function initDslToSql(wasmContent: string): Promise<void> {
    let encodedBinaryString = Buffer.from(wasmContent, "base64");
    let binaryString = pako.inflate(encodedBinaryString, { to: "string" });
    const goWasm = new window.Go();
    const result = await WebAssembly.instantiate(
        Buffer.from(binaryString, "base64"),
        goWasm.importObject
    );
    goWasm.run(result.instance);
}
