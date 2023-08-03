const initCalcWasm = async () => {
    {{ wasm_exec_js }}
    let binaryString = atob("{{file_base64}}");
    let bytes = new Uint8Array(binaryString.length);
    for (var i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    let arrayBuffer = bytes.buffer;

    const go = new window.Go();
    const result = await WebAssembly.instantiate(arrayBuffer, go.importObject);
    go.run(result.instance);
}
