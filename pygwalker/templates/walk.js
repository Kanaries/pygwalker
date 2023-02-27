var gw_id = "gwalker-{{ gwalker.id }}";
var props = {{ gwalker.props }};
console.log(props, gw_id);
GraphicWalker.GWalker(props, gw_id);
try{
}catch(e){ console.error(e); }