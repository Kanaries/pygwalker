var gw_id = "gwalker-{{ gwalker.id }}";
var props = {{ gwalker.props }};
console.log(PyGWalkerApp, props, gw_id);
try{
PyGWalkerApp.GWalker(props, gw_id);
}catch(e){ console.error(e); }