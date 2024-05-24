"""
pygwalker>=0.4.8.6

This is poc for PygWalker integration with FastAPI.

If you want to use Graphic-Walker in your web application, the best practice is to use Graphic-Walker as a separate front-end component for development, rather than using pygwalker.

run it: uvicorn web_server_demo:app --reload --port 8000
view it: http://127.0.0.1:8000/pyg_html/test0
"""
from typing import Dict, Any
import json

from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse, JSONResponse
from pygwalker.api.pygwalker import PygWalker
from pygwalker.communications.base import BaseCommunication
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker import GlobalVarManager
import pandas as pd

app = FastAPI()


def init_pygwalker_entity_map() -> Dict[str, PygWalker]:
    """Register PygWalker entity"""
    GlobalVarManager.set_privacy("offline")
    df = pd.read_csv("https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv")
    walker = PygWalker(
        gid="test0",
        dataset=df,
        field_specs=None,
        spec="",
        source_invoke_code="",
        theme_key="vega",
        appearance="light",
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=True,
        use_save_tool=False,
        is_export_dataframe=False,
        kanaries_api_key="",
        default_tab="vis",
        cloud_computation=False,
        gw_mode="explore",
    )
    comm = BaseCommunication(walker.gid)
    walker._init_callback(comm)
    return {
        walker.gid: walker
    }


pygwalker_entity_map = init_pygwalker_entity_map()


@app.post("/_pygwalker/comm/{gid}")
def pygwalker_comm(gid: str, payload: Dict[str, Any] = Body(...)):
    if gid not in pygwalker_entity_map:
        return {"success": False, "message": f"Unknown gid: {gid}"}

    comm_obj = pygwalker_entity_map[gid].comm
    result = comm_obj._receive_msg(payload["action"], payload["data"])
    return JSONResponse(content=json.loads(json.dumps(result, cls=DataFrameEncoder)))


@app.get("/pyg_html/{gid}")
def pyg_html(gid: str):
    walker = pygwalker_entity_map[gid]
    props = walker._get_props("web_server")
    props["communicationUrl"] = "_pygwalker/comm"
    html = walker._get_render_iframe(props, True)
    return HTMLResponse(content=html)
