try{
var gw_id = "gwalker-{{ gwalker.id }}";
var props = {{ gwalker.props }};
props.dataSource = props.dataSource.data.map(record => props.dataSource.columns.map((col, i) => ({ [col]: i })));
console.log(props, gw_id);
GraphicWalker.GWalker(props, gw_id);
}catch(e){ console.error(e); }