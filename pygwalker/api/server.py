import json
import webbrowser
import threading
import time
from typing import Union, List, Optional, Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.free_port import find_free_port
from pygwalker.communications.base import BaseCommunication


def create_fastapi_server(walker: PygWalker) -> FastAPI:
    """Create a high-performance FastAPI server to serve a PygWalker instance to the browser."""
    app = FastAPI(title="PyGWalker Fast Server (Jupyter Bypass)")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize communication handler
    walker.use_preview = False
    walker._init_callback(BaseCommunication(str(walker.gid)))

    @app.get("/", response_class=HTMLResponse)
    async def get_index():
        props = walker._get_props("web_server")
        props["communicationUrl"] = "/comm"
        # Render HTML without jupyter iframe wrapping if desired, or with iframe
        html = walker._get_render_iframe(props, return_iframe=False)
        return HTMLResponse(content=html, status_code=200)

    @app.post("/comm")
    async def post_comm(request: Request):
        payload = await request.json()
        action = payload.get("action", "")
        data = payload.get("data", {})
        
        # Handle message via communication handler
        result = walker.comm._receive_msg(action, data)
        encoded_json = json.dumps(result, cls=DataFrameEncoder)
        return Response(content=encoded_json, media_type="application/json")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "gid": str(walker.gid)}

    return app


def walk_server(
    dataset: Union[DataFrame, Any],
    gid: Optional[Union[int, str]] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec: str = "",
    spec_path: Optional[str] = None,
    port: Optional[int] = None,
    auto_open: bool = True,
    **kwargs,
) -> None:
    """Launch PyGWalker as a standalone FastAPI web server directly in the browser (No Jupyter required)."""
    if field_specs is None:
        field_specs = []

    if port is None:
        port = find_free_port()

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=True,
        use_save_tool=True,
        gw_mode="explore",
        is_export_dataframe=True,
        kanaries_api_key="",
        default_tab="vis",
        cloud_computation=False,
        **kwargs,
    )

    app = create_fastapi_server(walker)
    url = f"http://localhost:{port}"

    def _open_browser():
        time.sleep(0.8)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    if auto_open:
        threading.Thread(target=_open_browser, daemon=True).start()

    print(f"\n🚀 PyGWalker Fast Server running at: {url}\nPress Ctrl+C to stop.\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
