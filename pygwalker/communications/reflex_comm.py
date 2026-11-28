import json
import logging

from fastapi import FastAPI
from starlette.responses import JSONResponse, Response
from starlette.requests import Request

from pygwalker.utils.encode import DataFrameEncoder
from .base import BaseCommunication
from .http_security import BoundedCommMap, CommRequestError, read_starlette_json

logger = logging.getLogger(__name__)

reflex_comm_map = BoundedCommMap()

# Fixed: Consistent path with leading slash to match mount point
BASE_URL_PATH = "/_pygwalker/comm"


async def _handle_comm_request(gid: str, request: Request) -> Response:
    try:
        json_data = await read_starlette_json(request)
        if not isinstance(json_data, dict) or not isinstance(json_data.get("action"), str):
            raise CommRequestError(400, "Expected a JSON object with a string action")

        comm_obj = reflex_comm_map.get(gid)
        if comm_obj is None:
            return JSONResponse({"success": False, "message": f"Unknown gid: {gid}"})

        result = comm_obj._receive_msg(json_data["action"], json_data.get("data", {}))
        encoded_result = json.loads(json.dumps(result, cls=DataFrameEncoder))
        return JSONResponse(encoded_result)
    except CommRequestError as e:
        return JSONResponse(e.to_payload(), status_code=e.status)
    except Exception:
        logger.exception("Unhandled error in Reflex PyGWalker endpoint")
        return JSONResponse({"success": False, "message": "Internal server error"}, status_code=500)


async def _pygwalker_router(req: Request) -> Response:
    """Legacy router function - kept for compatibility."""
    return await _handle_comm_request(req.path_params["gid"], req)


class ReflexCommunication(BaseCommunication):
    """Communication class for Reflex."""

    allow_open_in_desktop = False

    def __init__(self, gid: str) -> None:
        super().__init__(gid)
        reflex_comm_map[gid] = self


# Create a FastAPI sub-application for PyGWalker API
def _create_pygwalker_app() -> FastAPI:
    """Create a FastAPI sub-application for PyGWalker API routes."""
    pygwalker_app = FastAPI()
    
    @pygwalker_app.post("/{gid}")
    async def pygwalker_endpoint(gid: str, request: Request) -> Response:
        """PyGWalker communication endpoint with proper error handling."""
        return await _handle_comm_request(gid, request)

    return pygwalker_app


def register_pygwalker_api(app: FastAPI) -> FastAPI:
    """Register pygwalker API route into Reflex app."""
    # Create a sub-application for PyGWalker routes
    pygwalker_app = _create_pygwalker_app()
    
    # Fixed: Use consistent path (BASE_URL_PATH already has leading slash)
    app.mount(BASE_URL_PATH, pygwalker_app)
    
    return app
