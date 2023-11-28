var gw_id = "{{ gwalker.id }}";
var props = {{ gwalker.props }};

window.__GW_VERSION=props.version;
PyGWalkerApp.PreviewApp(props, gw_id);
