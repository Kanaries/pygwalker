var gw_id = "gwalker-div-{{ gwalker.id }}";
var props = {{ gwalker.props }};
console.log(PyGWalkerApp, props, gw_id);

const initFunc = async () => {
    await initCalcWasm();
};

try{
    window.__GW_HASH=props.hashcode;
    window.__GW_VERSION=props.version;
    initFunc().then(() => {
        PyGWalkerApp.GWalker(props, gw_id);
    });
} catch(e) {
    console.error(e);
}