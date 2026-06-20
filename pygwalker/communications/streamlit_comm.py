import gc
import json
import re

from tornado.web import Application
from streamlit import config

try:
    from streamlit.web.server.server_util import make_url_path_regex as _streamlit_make_url_path_regex
except ImportError:  # pragma: no cover - depends on the installed Streamlit version.
    _streamlit_make_url_path_regex = None
import tornado.web
import streamlit as st

try:
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
except ImportError:  # pragma: no cover - depends on the installed Streamlit stack.
    Starlette = None
    JSONResponse = None
    Mount = None
    Route = None

from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.errors import StreamlitPygwalkerApiError
from .base import BaseCommunication

streamlit_comm_map = {}

_STREAMLIT_PREFIX_URL = config.get_option("server.baseUrlPath").strip("/")
BASE_URL_PATH = "/_stcore/_pygwalker/comm/".strip("/")
STREAMLIT_API_ROUTE = "/_stcore/_pygwalker/comm/{gid}"


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
        comm_obj = streamlit_comm_map.get(gid, None)
        if comm_obj is None:
            self.write({"success": False, "message": f"Unknown gid: {gid}"})
            return
        json_data = json.loads(self.request.body)

        # pylint: disable=protected-access
        result = comm_obj._receive_msg_envelope(json_data)
        # pylint: enable=protected-access

        self.write(json.dumps(result, cls=DataFrameEncoder))
        return


async def _pygwalker_router(req):
    gid = req.path_params["gid"]
    comm_obj = streamlit_comm_map.get(gid, None)
    if comm_obj is None:
        return JSONResponse({"success": False, "message": f"Unknown gid: {gid}"})
    json_data = await req.json()

    # pylint: disable=protected-access
    result = comm_obj._receive_msg_envelope(json_data)
    # pylint: enable=protected-access

    result = json.dumps(result, cls=DataFrameEncoder)
    return JSONResponse(json.loads(result))


def _register_tornado_handler() -> bool:
    tornado_obj = None
    for obj in gc.get_objects():
        try:
            if isinstance(obj, Application) and any(
                ("streamlit" in str(rule.target) for rule in obj.wildcard_router.rules)
            ):
                tornado_obj = obj
        except Exception:
            pass

    if tornado_obj is None:
        return False

    tornado_obj.add_handlers(".*", [(PYGWALKER_API_PATH, PygwalkerHandler)])
    return True


def _get_starlette_routes(app):
    router = getattr(app, "router", None)
    if router is not None and hasattr(router, "routes"):
        return router.routes
    return getattr(app, "routes", None)


def _is_streamlit_starlette_app(app) -> bool:
    routes = _get_starlette_routes(app)
    if routes is None:
        return False
    return any("_stcore" in getattr(route, "path", "") or "streamlit" in getattr(route, "path", "") for route in routes)


def _register_starlette_route() -> bool:
    if Starlette is None or Route is None:
        return False

    for obj in gc.get_objects():
        try:
            if not isinstance(obj, Starlette) or not _is_streamlit_starlette_app(obj):
                continue
            routes = _get_starlette_routes(obj)
            if routes is None:
                continue
            for index, route in enumerate(routes):
                if getattr(route, "path", None) == STREAMLIT_API_ROUTE:
                    routes[index] = Route(STREAMLIT_API_ROUTE, _pygwalker_router, methods=["POST"])
                    return True

            pygwalker_route = Route(STREAMLIT_API_ROUTE, _pygwalker_router, methods=["POST"])
            static_mount_index = next(
                (
                    index
                    for index, route in enumerate(routes)
                    if Mount is not None and isinstance(route, Mount) and getattr(route, "path", None) in {"", "/"}
                ),
                None,
            )
            if static_mount_index is None:
                routes.append(pygwalker_route)
            else:
                routes.insert(static_mount_index, pygwalker_route)
            return True
        except Exception:
            pass

    return False


def _hack_streamlit_server_impl():
    if _register_tornado_handler():
        return
    if _register_starlette_route():
        return
    raise StreamlitPygwalkerApiError()


@st.cache_resource
def hack_streamlit_server():
    _hack_streamlit_server_impl()


class StreamlitCommunication(BaseCommunication):
    """
    Hacker streamlit communication class.
    only support receive message.
    """

    def __init__(self, gid: str) -> None:
        super().__init__(gid)
        streamlit_comm_map[gid] = self
