var gw_id = "gwalker-{{ gwalker.id }}";
var props = {{ gwalker.props }};
console.log(PyGWalkerApp, props, gw_id);
function updateHeight() {
  window.parent.postMessage({iframeToResize: "gwalker-{{ gwalker.id }}", desiredHeight: Math.max(document.documentElement.scrollHeight, document.documentElement.offsetHeight, document.documentElement.clientHieght)}, '*');
}
window.addEventListener('load', function() {
  if(window.ResizeObserver) {
    var obs = new ResizeObserver(updateHeight);
    obs.observe(document.body);
  } else {
    setInterval(updateHeight, 2000);
  }
});
window.addEventListener('resize', updateHeight); 

try{
window.__GW_HASH=props.hashcode;
window.__GW_VERSION=props.version;
PyGWalkerApp.GWalker(props, gw_id);
}catch(e){ console.error(e); }