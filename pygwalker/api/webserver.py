from typing import Union, List, Optional, TYPE_CHECKING
import threading
import socketserver
import http.server
import urllib.parse
import json
import webbrowser
import time

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IComputation, IThemeKey
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils.computation import resolve_computation_mode
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.free_port import find_free_port
from pygwalker.utils.spec import resolve_spec_input
from pygwalker.communications.base import BaseCommunication
from pygwalker.api._walker_reuse import (
    collect_walker_construction_conflicts,
    get_callable_defaults,
    is_public_walker,
    reject_walker_construction_params,
)

if TYPE_CHECKING:
    from pygwalker.api.walker import Walker

_MAX_HEALTH_TIMEOUT_SECONDS = 3
_SEND_HEALTH_JS_SCRIPT = """
<script>
    setInterval(() => {
        fetch("/health", { method: "GET" })
            .then(response => {
                if (!response.ok) {
                    window.close();
                }
            })
            .catch(error => {
                window.close();
            });
    }, 1000);
</script>
"""


class _GlobalState:
    def __init__(self, auto_shutdown: bool):
        # why +60? If page not auto open, user manually open page, we should give user more time to interact with page.
        self.last_health_time = time.time() + 60
        self.auto_shutdown = auto_shutdown


class _PygWalkerHandler(http.server.SimpleHTTPRequestHandler):
    _walker: PygWalker
    _state: _GlobalState

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/health":
            self._state.last_health_time = time.time()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            return

        props = self._walker._get_props("web_server")
        props["communicationUrl"] = "comm"

        html = self._walker._get_render_iframe(props)
        if self._state.auto_shutdown:
            html += _SEND_HEALTH_JS_SCRIPT

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if not path.startswith("/comm"):
            self.send_error(404)
            return

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")
        payload = json.loads(post_data)
        result = self._walker.comm._receive_msg_envelope(payload)
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result, cls=DataFrameEncoder).encode("utf-8"))

    def log_message(self, format, *args):
        pass


class CustomTCPServer(socketserver.TCPServer):
    def log_request(self, *args, **kwargs):
        pass


def _create_handler_with_walker(walker: PygWalker, state: _GlobalState):
    """Create a custom handler with walker"""

    class CustomPygWalkerHandler(_PygWalkerHandler):
        _walker = walker
        _state = state

    return CustomPygWalkerHandler


def _reject_walker_construction_params(
    *,
    gid: Optional[Union[int, str]],
    field_specs: Optional[List[FieldSpec]],
    theme_key: IThemeKey,
    appearance: IAppearance,
    spec: str,
    spec_path: Optional[str],
    computation: Optional[IComputation],
    use_kernel_calc: Optional[bool],
    kernel_computation: Optional[bool],
    cloud_computation: bool,
    show_cloud_tool: bool,
    kanaries_api_key: str,
    default_tab: Literal["data", "vis"],
    kwargs,
) -> None:
    values = {
        "gid": gid,
        "field_specs": field_specs,
        "theme_key": theme_key,
        "appearance": appearance,
        "spec": spec,
        "spec_path": spec_path,
        "computation": computation,
        "use_kernel_calc": use_kernel_calc,
        "kernel_computation": kernel_computation,
        "cloud_computation": cloud_computation,
        "show_cloud_tool": show_cloud_tool,
        "kanaries_api_key": kanaries_api_key,
        "default_tab": default_tab,
    }
    conflicts = collect_walker_construction_conflicts(
        values,
        get_callable_defaults(walk, values),
        conflict_predicates={
            "cloud_computation": lambda value: value not in (False, None),
            "show_cloud_tool": lambda value: value is not True,
        },
        extra_kwargs=kwargs,
    )
    reject_walker_construction_params("webserver.walk()", conflicts)


def _open_browser(address: str, delay_ms: int = 1000):
    """Open browser with address"""
    time.sleep(delay_ms / 1000)

    try:
        opened = webbrowser.open(address)
    except Exception:
        opened = False

    if opened:
        print(f"Run pygwalker at {address}, close page or press Ctrl+C to end.")
    else:
        print(f"Auto open browser failed, please open {address} manually, close page or press Ctrl+C to end.")


def _start_server(
    walker: PygWalker,
    port: Optional[int],
    *,
    auto_open: bool,
    auto_shutdown: bool,
):
    """Start a server with walker"""
    state = _GlobalState(auto_shutdown=auto_shutdown)
    walker.use_preview = False
    walker._init_callback(BaseCommunication(str(walker.gid)))

    handler = _create_handler_with_walker(walker, state)
    if port is None:
        port = find_free_port()
    address = f"http://localhost:{port}"

    def _listen_shutdown():
        while 1:
            time.sleep(1)
            if time.time() - state.last_health_time > _MAX_HEALTH_TIMEOUT_SECONDS:
                httpd.shutdown()
                break

    try:
        with CustomTCPServer(("127.0.0.1", port), handler) as httpd:
            if auto_open:
                threading.Thread(target=_open_browser, args=(address,), daemon=True).start()
            if auto_shutdown:
                threading.Thread(target=_listen_shutdown, daemon=True).start()
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass


def walk(
    dataset: Union[DataFrame, Connector, str, "Walker"],
    gid: Optional[Union[int, str]] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec: str = "",
    spec_path: Optional[str] = None,
    computation: Optional[IComputation] = None,
    use_kernel_calc: Optional[bool] = None,
    kernel_computation: Optional[bool] = None,
    cloud_computation: bool = False,
    show_cloud_tool: bool = True,
    kanaries_api_key: str = "",
    default_tab: Literal["data", "vis"] = "vis",
    port: Optional[int] = None,
    auto_shutdown: bool = False,
    auto_open: bool = False,
    **kwargs,
):
    """Walk through a tabular dataset with Graphic Walker.
    This function was originally designed solely to launch Pygwalker in script mode.

    Args:
        - dataset (pandas.DataFrame | polars.DataFrame | pyarrow.Table | Connector | str | pygwalker.Walker, optional): dataset or reusable Walker object.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - theme_key ('vega' | 'g2' | 'streamlit'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - spec_path (str): local chart configuration file path. Prefer this over passing a file path through `spec`.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "auto".
        - use_kernel_calc(bool): Deprecated alias for kernel computation. Prefer computation="kernel".
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None, automatically determine whether to use kernel calculation.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
        - cloud_computation(bool): Whether to use cloud compute for datas, it upload your data to kanaries cloud. Default to False.
        - port (int): port to use for the server. Default to None, which means a random port will be used.
        - auto_shutdown (bool): Whether to shutdown the server when the page is closed. Default to False.
        - auto_open (bool): Whether to open the browser automatically. Default to False.
    """
    check_expired_params(kwargs)

    if is_public_walker(dataset):
        _reject_walker_construction_params(
            gid=gid,
            field_specs=field_specs,
            theme_key=theme_key,
            appearance=appearance,
            spec=spec,
            spec_path=spec_path,
            computation=computation,
            use_kernel_calc=use_kernel_calc,
            kernel_computation=kernel_computation,
            cloud_computation=cloud_computation,
            show_cloud_tool=show_cloud_tool,
            kanaries_api_key=kanaries_api_key,
            default_tab=default_tab,
            kwargs=kwargs,
        )
        _start_server(dataset.core, port, auto_open=auto_open, auto_shutdown=auto_shutdown)
        return

    if field_specs is None:
        field_specs = []

    resolved_spec = resolve_spec_input(spec, spec_path)
    resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
        dataset,
        computation=computation,
        use_kernel_calc=use_kernel_calc,
        kernel_computation=kernel_computation,
        cloud_computation=cloud_computation,
    )

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=resolved_spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=show_cloud_tool,
        use_preview=False,
        kernel_computation=resolved_kernel_computation,
        use_save_tool=True,
        gw_mode="explore",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=resolved_cloud_computation,
        **kwargs,
    )
    _start_server(walker, port, auto_open=auto_open, auto_shutdown=auto_shutdown)


def render(
    dataset: Union[DataFrame, Connector, str],
    spec: str = "",
    *,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec_path: Optional[str] = None,
    computation: Optional[IComputation] = None,
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    port: Optional[int] = None,
    auto_shutdown: bool = False,
    auto_open: bool = False,
    **kwargs,
):
    """
    This function was originally designed solely to launch Pygwalker in script mode.

    Args:
        - dataset (pandas.DataFrame | polars.DataFrame | pyarrow.Table | Connector | str, optional): dataset.
        - spec (str): chart config data. config id, json, remote file url
        - spec_path (str): local chart configuration file path. Prefer this over passing a file path through `spec`.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "auto".
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - port (int): port to use for the server. Default to None, which means a random port will be used.
        - auto_shutdown (bool): Whether to shutdown the server when the page is closed. Default to False.
        - auto_open (bool): Whether to open the browser automatically. Default to False.
    """
    resolved_spec = resolve_spec_input(spec, spec_path)
    resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
        dataset,
        computation=computation,
        kernel_computation=kernel_computation,
    )

    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=[],
        spec=resolved_spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=resolved_kernel_computation,
        use_save_tool=False,
        gw_mode="filter_renderer",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab="vis",
        cloud_computation=resolved_cloud_computation,
        **kwargs,
    )
    _start_server(walker, port, auto_open=auto_open, auto_shutdown=auto_shutdown)


def table(
    dataset: Union[DataFrame, Connector, str],
    *,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec_path: Optional[str] = None,
    computation: Optional[IComputation] = None,
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    port: Optional[int] = None,
    auto_shutdown: bool = False,
    auto_open: bool = False,
    **kwargs,
):
    """
    This function was originally designed solely to launch Pygwalker in script mode.

    Args:
        - dataset (pandas.DataFrame | polars.DataFrame | pyarrow.Table | Connector | str, optional): dataset.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec_path (str): local chart configuration file path.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "auto".
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - port (int): port to use for the server. Default to None, which means a random port will be used.
        - auto_shutdown (bool): Whether to shutdown the server when the page is closed. Default to False.
        - auto_open (bool): Whether to open the browser automatically. Default to False.
    """
    resolved_spec = resolve_spec_input("", spec_path)
    resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
        dataset,
        computation=computation,
        kernel_computation=kernel_computation,
    )
    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=[],
        spec=resolved_spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=resolved_kernel_computation,
        use_save_tool=False,
        gw_mode="table",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab="vis",
        cloud_computation=resolved_cloud_computation,
        **kwargs,
    )
    _start_server(walker, port, auto_open=auto_open, auto_shutdown=auto_shutdown)
