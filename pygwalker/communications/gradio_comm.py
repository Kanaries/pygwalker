import json
import gc

from fastapi import FastAPI
from starlette.routing import Route
from starlette.responses import JSONResponse, Response
from starlette.requests import Request

from pygwalker.utils.encode import DataFrameEncoder
from .base import BaseCommunication
from .http_security import BoundedCommMap, CommRequestError, read_starlette_json

gradio_comm_map = BoundedCommMap()

BASE_URL_PATH = "/_pygwalker/comm/".strip("/")


async def _pygwalker_router(req: Request) -> Response:
    gid = req.path_params["gid"]
    try:
        json_data = await read_starlette_json(req)
        if not isinstance(json_data, dict) or not isinstance(json_data.get("action"), str):
            raise CommRequestError(400, "Expected a JSON object with a string action")
    except CommRequestError as e:
        return JSONResponse(e.to_payload(), status_code=e.status)

    comm_obj = gradio_comm_map.get(gid, None)
    if comm_obj is None:
        return JSONResponse({"success": False, "message": f"Unknown gid: {gid}"})

    # pylint: disable=protected-access
    result = comm_obj._receive_msg(json_data["action"], json_data.get("data", {}))
    # pylint: enable=protected-access

    result = json.dumps(result, cls=DataFrameEncoder)
    return JSONResponse(json.loads(result))


class GradioCommunication(BaseCommunication):
    """
    Hacker streamlit communication class.
    only support receive message.
    """
    allow_open_in_desktop = False

    def __init__(self, gid: str) -> None:
        super().__init__(gid)
        gradio_comm_map[gid] = self


PYGWALKER_ROUTE = Route(
    "/_pygwalker/comm/{gid}",
    _pygwalker_router,
    methods=["POST"]
)


# it will work when gradio server reload
def _hack_gradio_server():
    for obj in gc.get_objects():
        if isinstance(obj, FastAPI):
            for index, route in enumerate(obj.routes):
                if route.path == "/_pygwalker/comm/{gid}":
                    obj.routes[index] = PYGWALKER_ROUTE
                    return


_hack_gradio_server()
