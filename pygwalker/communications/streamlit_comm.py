import gc
import json

from tornado.web import Application
from streamlit import config
from streamlit.web.server.server_util import make_url_path_regex
import tornado.web
import streamlit as st

from pygwalker.utils.encode import DataFrameEncoder
from .base import BaseCommunication

streamlit_comm_map = {}

_STREAMLIT_PREFIX_URL = config.get_option("server.baseUrlPath").strip("/")
BASE_URL_PATH = (_STREAMLIT_PREFIX_URL + "/_stcore/_pygwalker/comm/").strip("/")
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
        self.write(
            json.dumps(
                comm_obj._receive_msg(json_data["action"], json_data["data"]),
                cls=DataFrameEncoder
            )
        )
        # pylint: enable=protected-access
        return


@st.cache_resource
def hack_streamlit_server():
    tornado_obj = None
    for obj in gc.get_objects():
        if isinstance(obj, Application):
            tornado_obj = obj
            break

    tornado_obj.add_handlers(".*", [(PYGWALKER_API_PATH, PygwalkerHandler)])


class StreamlitCommunication(BaseCommunication):
    """
    Hacker streamlit communication class.
    only support receive message.
    """
    def __init__(self, gid: str) -> None:
        super().__init__()
        streamlit_comm_map[gid] = self
        self.gid = gid
