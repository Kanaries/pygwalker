from typing import Union, List, Optional
import hmac
import http.cookies
import logging
import secrets
import sys
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
from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.free_port import find_free_port
from pygwalker.communications.base import BaseCommunication
from pygwalker.communications.http_security import (
    has_custom_request_header,
    is_allowed_local_host,
    is_json_content_type,
    is_same_origin,
    parse_content_length,
)

logger = logging.getLogger(__name__)

AUTH_COOKIE_NAME = "pygwalker_token"
_MAX_HEALTH_TIMEOUT_SECONDS = 3
_SEND_HEALTH_JS_SCRIPT = """
<script>
    setInterval(() => {
        fetch("/health", { method: "GET", credentials: "same-origin" })
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
    def __init__(self, auto_shutdown: bool, auth_token: Optional[str] = None):
        # why +60? If page not auto open, user manually open page, we should give user more time to interact with page.
        self.last_health_time = time.time() + 60
        self.auto_shutdown = auto_shutdown
        # Per-server secret. It is handed out once in the printed URL and then kept in an
        # HttpOnly cookie, so other local users/processes and web pages cannot drive the server.
        self.auth_token = auth_token or secrets.token_urlsafe(32)
        # The server is threaded (so a stalled client cannot block it), but walker / data parser
        # state is not guaranteed to be thread-safe, so comm dispatch is serialized.
        self.comm_lock = threading.Lock()


class _PygWalkerHandler(http.server.BaseHTTPRequestHandler):
    """Minimal, authenticated HTTP handler. Never serves files from disk."""

    timeout = 30
    _walker: PygWalker
    _state: _GlobalState

    # ---- helpers -------------------------------------------------------------------------

    def _send_body(self, status: int, body: bytes, content_type: str, extra_headers=None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for name, value in extra_headers or ():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_text(self, status: int, message: str, extra_headers=None) -> None:
        self._send_body(status, message.encode("utf-8"), "text/plain; charset=utf-8", extra_headers)

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload, cls=DataFrameEncoder).encode("utf-8")
        self._send_body(status, body, "application/json; charset=utf-8")

    def _is_valid_token(self, token: Optional[str]) -> bool:
        if not token:
            return False
        return hmac.compare_digest(token.encode("utf-8"), self._state.auth_token.encode("utf-8"))

    def _has_valid_cookie(self) -> bool:
        raw_cookie = self.headers.get("Cookie")
        if not raw_cookie:
            return False
        cookie = http.cookies.SimpleCookie()
        try:
            cookie.load(raw_cookie)
        except http.cookies.CookieError:
            return False
        morsel = cookie.get(AUTH_COOKIE_NAME)
        return morsel is not None and self._is_valid_token(morsel.value)

    def _check_host_and_origin(self) -> bool:
        """Reject DNS-rebinding (bad Host) and cross-origin (bad Origin) requests."""
        host = self.headers.get("Host")
        if not is_allowed_local_host(host):
            self._send_text(403, "Forbidden: invalid Host header")
            return False
        if not is_same_origin(self.headers.get("Origin"), host):
            self._send_text(403, "Forbidden: cross-origin request")
            return False
        return True

    def parse_request(self):
        # Check every parsed request, including methods handled by the stdlib.
        return super().parse_request() and self._check_host_and_origin()

    def _is_comm_path(self, path: str) -> bool:
        return path in ("/comm", f"/comm/{self._walker.gid}")

    # ---- methods -------------------------------------------------------------------------

    def do_GET(self):
        parsed_path = urllib.parse.urlsplit(self.path)
        path = parsed_path.path

        if path == "/":
            tokens = urllib.parse.parse_qs(parsed_path.query).get("token")
            if tokens and self._is_valid_token(tokens[0]):
                cookie = f"{AUTH_COOKIE_NAME}={self._state.auth_token}; HttpOnly; SameSite=Strict; Path=/"
                # Drop the token from the address bar / history as soon as it has been exchanged.
                self._send_text(302, "Found", [("Location", "/"), ("Set-Cookie", cookie)])
                return
            if not self._has_valid_cookie():
                self._send_text(403, "Forbidden: open the URL (with token) printed in the terminal.")
                return
            self._send_index()
            return

        if path == "/health":
            if not self._has_valid_cookie():
                self._send_text(403, "Forbidden")
                return
            self._state.last_health_time = time.time()
            self._send_text(200, "OK")
            return

        self._send_text(404, "Not Found")

    def _send_index(self) -> None:
        props = self._walker._get_props("web_server")
        props["communicationUrl"] = "comm"

        html = self._walker._get_render_iframe(props)
        if self._state.auto_shutdown:
            html += _SEND_HEALTH_JS_SCRIPT

        self._send_body(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)

        if not self._is_comm_path(path):
            self._send_text(404, "Not Found")
            return
        if not self._has_valid_cookie():
            self._send_json(403, {"success": False, "message": "Forbidden"})
            return
        if not has_custom_request_header(self.headers):
            self._send_json(403, {"success": False, "message": "Missing X-PyGWalker-Request header"})
            return
        if not is_json_content_type(self.headers.get("Content-Type")):
            self._send_json(415, {"success": False, "message": "Content-Type must be application/json"})
            return
        content_length, error_status = parse_content_length(self.headers.get("Content-Length"))
        if error_status is not None:
            message = "Request body too large" if error_status == 413 else "Invalid Content-Length header"
            self._send_json(error_status, {"success": False, "message": message})
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            self._send_json(400, {"success": False, "message": "Invalid JSON in request body"})
            return

        if not isinstance(payload, dict) or not isinstance(payload.get("action"), str):
            self._send_json(400, {"success": False, "message": "Expected a JSON object with a string action"})
            return
        with self._state.comm_lock:
            result = self._walker.comm._receive_msg(payload["action"], payload.get("data", {}))
        self._send_json(200, result)

    def _reject_method(self):
        self._send_text(405, "Method Not Allowed", [("Allow", "GET, POST")])

    do_HEAD = _reject_method
    do_PUT = _reject_method
    do_DELETE = _reject_method
    do_PATCH = _reject_method
    do_OPTIONS = _reject_method

    def log_message(self, format, *args):
        pass


class CustomTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    # On Windows SO_REUSEADDR lets another process bind the same port and hijack traffic.
    allow_reuse_address = sys.platform != "win32"

    def log_request(self, *args, **kwargs):
        pass


def _create_handler_with_walker(walker: PygWalker, state: _GlobalState):
    """Create a custom handler with walker"""

    class CustomPygWalkerHandler(_PygWalkerHandler):
        _walker = walker
        _state = state

    return CustomPygWalkerHandler


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

    def _listen_shutdown():
        while 1:
            time.sleep(1)
            if time.time() - state.last_health_time > _MAX_HEALTH_TIMEOUT_SECONDS:
                httpd.shutdown()
                break

    try:
        walker._init_callback(BaseCommunication(str(walker.gid)))

        handler = _create_handler_with_walker(walker, state)
        if port is None:
            port = find_free_port()
        address = f"http://localhost:{port}/?token={state.auth_token}"
        with CustomTCPServer(("127.0.0.1", port), handler) as httpd:
            if auto_open:
                threading.Thread(target=_open_browser, args=(address,), daemon=True).start()
            else:
                print(f"Run pygwalker at {address}, press Ctrl+C to end.")
            if auto_shutdown:
                threading.Thread(target=_listen_shutdown, daemon=True).start()
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _close_walker_data_parser(walker)


def _close_walker_data_parser(walker: PygWalker) -> None:
    data_parser = getattr(walker, "data_parser", None)
    close = getattr(data_parser, "close", None)
    if not callable(close):
        return
    try:
        close()
    except Exception:
        logger.exception("Failed to close PyGWalker data parser")


def walk(
    dataset: Union[DataFrame, Connector, str],
    gid: Optional[Union[int, str]] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    spec: str = "",
    kernel_computation: Optional[bool] = None,
    cloud_computation: bool = False,
    show_cloud_tool: bool = True,
    kanaries_api_key: str = "",
    default_tab: Literal["data", "vis"] = "vis",
    port: Optional[int] = None,
    auto_shutdown: bool = False,
    auto_open: bool = False,
    **kwargs
):
    """Walk through pandas.DataFrame df with Graphic Walker.
    This function was originally designed solely to launch Pygwalker in script mode.

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - theme_key ('vega' | 'g2' | 'streamlit'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None, automatically determine whether to use kernel calculation.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
        - cloud_computation(bool): Whether to use cloud compute for datas, it upload your data to kanaries cloud. Default to False.
        - port (int): port to use for the server. Default to None, which means a random port will be used.
        - auto_shutdown (bool): Whether to shutdown the server when the page is closed. Default to False.
        - auto_open (bool): Whether to open the browser automatically. Default to False.
    """
    check_expired_params(kwargs)

    if field_specs is None:
        field_specs = []

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=show_cloud_tool,
        use_preview=False,
        kernel_computation=kernel_computation,
        use_save_tool=True,
        gw_mode="explore",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=cloud_computation,
        **kwargs
    )
    _start_server(walker, port, auto_open=auto_open, auto_shutdown=auto_shutdown)


def render(
    dataset: Union[DataFrame, Connector, str],
    spec: str,
    *,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    port: Optional[int] = None,
    auto_shutdown: bool = False,
    auto_open: bool = False,
    **kwargs
):
    """
    This function was originally designed solely to launch Pygwalker in script mode.

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - spec (str): chart config data. config id, json, remote file url

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - port (int): port to use for the server. Default to None, which means a random port will be used.
        - auto_shutdown (bool): Whether to shutdown the server when the page is closed. Default to False.
        - auto_open (bool): Whether to open the browser automatically. Default to False.
    """

    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=[],
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=isinstance(dataset, (Connector, str)) or kernel_computation,
        use_save_tool=False,
        gw_mode="filter_renderer",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab="vis",
        cloud_computation=False,
        **kwargs
    )
    _start_server(walker, port, auto_open=auto_open, auto_shutdown=auto_shutdown)


def table(
    dataset: Union[DataFrame, Connector, str],
    *,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    port: Optional[int] = None,
    auto_shutdown: bool = False,
    auto_open: bool = False,
    **kwargs
):
    """
    This function was originally designed solely to launch Pygwalker in script mode.

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - port (int): port to use for the server. Default to None, which means a random port will be used.
        - auto_shutdown (bool): Whether to shutdown the server when the page is closed. Default to False.
        - auto_open (bool): Whether to open the browser automatically. Default to False.
    """
    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=[],
        spec="",
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=isinstance(dataset, (Connector, str)) or kernel_computation,
        use_save_tool=False,
        gw_mode="table",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab="vis",
        cloud_computation=False,
        **kwargs
    )
    _start_server(walker, port, auto_open=auto_open, auto_shutdown=auto_shutdown)
