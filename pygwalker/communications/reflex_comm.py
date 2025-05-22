import json
from fastapi import FastAPI
from starlette.routing import Route
from starlette.responses import JSONResponse, Response
from starlette.requests import Request

from pygwalker.utils.encode import DataFrameEncoder
from .base import BaseCommunication

reflex_comm_map = {}

BASE_URL_PATH = "/_pygwalker/comm/".strip("/")


async def _pygwalker_router(req: Request) -> Response:
    gid = req.path_params["gid"]
    comm_obj = reflex_comm_map.get(gid, None)
    if comm_obj is None:
        return JSONResponse({"success": False, "message": f"Unknown gid: {gid}"})
    json_data = await req.json()
    result = comm_obj._receive_msg(json_data["action"], json_data["data"])
    result = json.dumps(result, cls=DataFrameEncoder)
    return JSONResponse(json.loads(result))


class ReflexCommunication(BaseCommunication):
    """Communication class for Reflex."""

    def __init__(self, gid: str) -> None:
        super().__init__(gid)
        reflex_comm_map[gid] = self


PYGWALKER_ROUTE = Route(
    "/_pygwalker/comm/{gid}",
    _pygwalker_router,
    methods=["POST"],
)


def register_pygwalker_api(app: FastAPI) -> None:
    """Register pygwalker API route into Reflex app."""
    app.router.routes.append(PYGWALKER_ROUTE)
