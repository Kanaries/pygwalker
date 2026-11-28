import gc
import json
import re

from tornado.web import Application
from streamlit import config
import tornado.web
import streamlit as st

try:
    from streamlit.web.server.server_util import make_url_path_regex as _streamlit_make_url_path_regex
except ImportError:  # pragma: no cover - depends on the installed Streamlit version.
    _streamlit_make_url_path_regex = None

from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.errors import StreamlitPygwalkerApiError
from .base import BaseCommunication
from .http_security import BoundedCommMap, CommRequestError, check_comm_request_headers, parse_json_body

streamlit_comm_map = BoundedCommMap()

_STREAMLIT_PREFIX_URL = config.get_option("server.baseUrlPath").strip("/")
BASE_URL_PATH = "/_stcore/_pygwalker/comm/".strip("/")

def _make_url_path_regex(base_path: str, path: str) -> str:
    if _streamlit_make_url_path_regex is not None:
        return _streamlit_make_url_path_regex(base_path, path)

    base_path = base_path.strip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    if base_path:
        return f"/{re.escape(base_path)}{path}"
    return path


PYGWALKER_API_PATH = _make_url_path_regex(_STREAMLIT_PREFIX_URL, r"/_stcore/_pygwalker/comm/(.+)")


class PygwalkerHandler(tornado.web.RequestHandler):
    """
    Handler for pygwalker communication
    """
    def check_xsrf_cookie(self):
        return True

    def post(self, gid: str):
        try:
            check_comm_request_headers(self.request.headers)
            json_data = parse_json_body(self.request.body or b"")
            if not isinstance(json_data, dict) or not isinstance(json_data.get("action"), str):
                raise CommRequestError(400, "Expected a JSON object with a string action")
        except CommRequestError as e:
            self.set_status(e.status)
            self.write(e.to_payload())
            return

        comm_obj = streamlit_comm_map.get(gid, None)
        if comm_obj is None:
            self.write({"success": False, "message": f"Unknown gid: {gid}"})
            return

        # pylint: disable=protected-access
        result = comm_obj._receive_msg(json_data["action"], json_data.get("data", {}))
        # pylint: enable=protected-access

        self.write(json.dumps(result, cls=DataFrameEncoder))
        return


@st.cache_resource
def hack_streamlit_server():
    tornado_obj = None
    for obj in gc.get_objects():
        try:
            if isinstance(obj, Application) and any(("streamlit" in str(rule.target) for rule in obj.wildcard_router.rules)):
                tornado_obj = obj
        except Exception:
            pass

    if tornado_obj:
        tornado_obj.add_handlers(".*", [(PYGWALKER_API_PATH, PygwalkerHandler)])
    else:
        raise StreamlitPygwalkerApiError()


class StreamlitCommunication(BaseCommunication):
    """
    Hacker streamlit communication class.
    only support receive message.
    """
    allow_open_in_desktop = False

    def __init__(self, gid: str) -> None:
        super().__init__(gid)
        streamlit_comm_map[gid] = self
