var gw_id = "gwalker-{{ gwalker.id }}";
var props = JSON.parse(`{{ gwalker.props }}`);
console.log(props, gw_id);
GraphicWalker.GWalker(props, gw_id);