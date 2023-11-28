var gw_id = "{{ gwalker.id }}";
var props = {{ gwalker.props }};
console.log(PyGWalkerApp, props, gw_id);

try{
    window.__GW_VERSION=props.version;
    PyGWalkerApp.GWalker(props, gw_id);
} catch(e) {
    console.error(e);
}