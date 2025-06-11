import json
from fastapi import FastAPI, HTTPException
from starlette.routing import Route
from starlette.responses import JSONResponse, Response
from starlette.requests import Request

from pygwalker.utils.encode import DataFrameEncoder
from .base import BaseCommunication

reflex_comm_map = {}

# Fixed: Consistent path with leading slash to match mount point
BASE_URL_PATH = "/_pygwalker/comm"


async def _pygwalker_router(req: Request) -> Response:
    """Legacy router function - kept for compatibility."""
    gid = req.path_params["gid"]
    comm_obj = reflex_comm_map.get(gid, None)
    if comm_obj is None:
        return JSONResponse({"success": False, "message": f"Unknown gid: {gid}"})
    
    try:
        json_data = await req.json()
        
        # Fixed: Input validation - check for required keys
        if "action" not in json_data:
            return JSONResponse({"success": False, "message": "Missing 'action' field in request"})
        if "data" not in json_data:
            return JSONResponse({"success": False, "message": "Missing 'data' field in request"})
        
        result = comm_obj._receive_msg(json_data["action"], json_data["data"])
        
        # Fixed: Proper JSON encoding with DataFrameEncoder
        encoded_result = json.loads(json.dumps(result, cls=DataFrameEncoder))
        return JSONResponse(encoded_result)
        
    except json.JSONDecodeError:
        return JSONResponse({"success": False, "message": "Invalid JSON in request body"})
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Internal error: {str(e)}"})


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
        """PyGWalker communication endpoint with proper error handling."""
        # Get the communication object for this gid
        comm_obj = reflex_comm_map.get(gid, None)
        if comm_obj is None:
            return JSONResponse({"success": False, "message": f"Unknown gid: {gid}"})
        
        try:
            # Process the request with validation
            json_data = await request.json()
            
            # Fixed: Input validation - check for required keys
            if "action" not in json_data:
                return JSONResponse({"success": False, "message": "Missing 'action' field in request"})
            if "data" not in json_data:
                return JSONResponse({"success": False, "message": "Missing 'data' field in request"})
            
            result = comm_obj._receive_msg(json_data["action"], json_data["data"])
            
            # Fixed: Proper JSON encoding with DataFrameEncoder
            encoded_result = json.loads(json.dumps(result, cls=DataFrameEncoder))
            return JSONResponse(encoded_result)
            
        except json.JSONDecodeError:
            return JSONResponse({"success": False, "message": "Invalid JSON in request body"})
        except Exception as e:
            return JSONResponse({"success": False, "message": f"Internal error: {str(e)}"})
    
    return pygwalker_app


def register_pygwalker_api(app: FastAPI) -> FastAPI:
    """Register pygwalker API route into Reflex app."""
    # Create a sub-application for PyGWalker routes
    pygwalker_app = _create_pygwalker_app()
    
    # Fixed: Use consistent path (BASE_URL_PATH already has leading slash)
    app.mount(BASE_URL_PATH, pygwalker_app)
    
    return app
