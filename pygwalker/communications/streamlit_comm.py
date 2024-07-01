import gc
import json

from tornado.web import Application
from streamlit import config
from streamlit.web.server.server_util import make_url_path_regex
import tornado.web
import streamlit as st

from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.errors import StreamlitPygwalkerApiError
from .base import BaseCommunication

streamlit_comm_map = {}

_STREAMLIT_PREFIX_URL = config.get_option("server.baseUrlPath").strip("/")
BASE_URL_PATH = "/_stcore/_pygwalker/comm/".strip("/")
PYGWALKER_API_PATH = make_url_path_regex(
    _STREAMLIT_PREFIX_URL,
    r"/_stcore/_pygwalker/comm/(.+)"
)


class PygwalkerHandler(tornado.web.RequestHandler):
    """
    Handler for pygwalker communication
    """
    def check_xsrf_cookie(self):
        return True

    def post(self, gid: str):
        comm_obj = streamlit_comm_map.get(gid, None)
        if comm_obj is None:
            self.write({"success": False, "message": f"Unknown gid: {gid}"})
            return
        json_data = json.loads(self.request.body)

        # pylint: disable=protected-access
        result = comm_obj._receive_msg(json_data["action"], json_data["data"])
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
    def __init__(self, gid: str) -> None:
        super().__init__(gid)
        streamlit_comm_map[gid] = self
