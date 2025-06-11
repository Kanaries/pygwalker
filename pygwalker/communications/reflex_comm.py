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


# Create a FastAPI sub-application for PyGWalker API
def _create_pygwalker_app() -> FastAPI:
    """Create a FastAPI sub-application for PyGWalker API routes."""
    pygwalker_app = FastAPI()
    
    @pygwalker_app.post("/{gid}")
    async def pygwalker_endpoint(gid: str, request: Request) -> Response:
        """PyGWalker communication endpoint."""
        # Get the communication object for this gid
        comm_obj = reflex_comm_map.get(gid, None)
        if comm_obj is None:
            return JSONResponse({"success": False, "message": f"Unknown gid: {gid}"})
        
        # Process the request
        json_data = await request.json()
        result = comm_obj._receive_msg(json_data["action"], json_data["data"])
        result = json.dumps(result, cls=DataFrameEncoder)
        return JSONResponse(json.loads(result))
    
    return pygwalker_app


def register_pygwalker_api(app: FastAPI) -> FastAPI:
    """Register pygwalker API route into Reflex app."""
    # Create a sub-application for PyGWalker routes
    pygwalker_app = _create_pygwalker_app()
    
    # Mount the sub-application at the PyGWalker API path
    app.mount("/_pygwalker/comm", pygwalker_app)
    
    return app
