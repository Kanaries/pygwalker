from typing import List, Dict, Any
from concurrent.futures.thread import ThreadPoolExecutor
import base64
import zlib
import json

from pydantic import BaseModel, Field
from ipylab import JupyterFrontEnd

from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.display import display_html
from pygwalker.utils.randoms import generate_hash_code
from pygwalker.services.render import jinja_env, GWALKER_SCRIPT_BASE64, compress_data


class ImgData(BaseModel):
    row_index: int = Field(..., alias="rowIndex")
    col_index: int = Field(..., alias="colIndex")
    data: str
    height: int
    width: int
    canvas_height: int = Field(..., alias="canvasHeight")
    canvas_width: int = Field(..., alias="canvasWidth")


class ChartData(BaseModel):
    charts: List[ImgData]
    single_chart: str = Field(..., alias="singleChart")
    n_rows: int = Field(..., alias="nRows")
    n_cols: int = Field(..., alias="nCols")
    title: str


def render_gw_preview_html(
    vis_spec_obj: List[Dict[str, Any]],
    datas: List[List[Dict[str, Any]]],
    theme_key: str,
    gid: str,
    appearance: str,
) -> str:
    """
    Render html for previewing gwalker(use purerenderer mode of graphic-wlaker, not png preview)
    """
    charts = []
    for vis_spec_item, data in zip(
        vis_spec_obj,
        datas
    ):
        charts.append({
            "visSpec": vis_spec_item,
            "data": data
        })

    props = {"charts": charts, "themeKey": theme_key, "dark": appearance, "gid": gid}

    container_id = f"pygwalker-preview-{gid}"
    template = jinja_env.get_template("pygwalker_main_page.html")
    html = template.render(
        gwalker={
            'id': container_id,
            'gw_script': GWALKER_SCRIPT_BASE64,
            "component_script": "PyGWalkerApp.PreviewApp(props, gw_id);",
            "props": compress_data(json.dumps(props, cls=DataFrameEncoder))
        },
        component_url=""
    )
    return html


def render_gw_chart_preview_html(
    *,
    single_vis_spec: Dict[str, Any],
    data: List[Dict[str, Any]],
    theme_key: str,
    title: str,
    desc: str,
    appearance: str,
) -> str:
    """
    Render html for single chart(use purerenderer mode of graphic-wlaker, not png preview)
    """

    props = {
        "visSpec": single_vis_spec,
        "data": data,
        "themeKey": theme_key,
        "title": title,
        "desc": desc,
        "dark": appearance,
    }

    container_id = f"pygwalker-chart-preview-{generate_hash_code()[:20]}"
    template = jinja_env.get_template("pygwalker_main_page.html")
    html = template.render(
        gwalker={
            'id': container_id,
            'gw_script': GWALKER_SCRIPT_BASE64,
            "component_script": "PyGWalkerApp.ChartPreviewApp(props, gw_id);",
            "props": compress_data(json.dumps(props, cls=DataFrameEncoder))
        },
        component_url=""
    )
    return html


class PreviewImageTool:
    """Preview image tool for pygwalker"""
    def __init__(self, gid: str):
        self.gid = gid
        self.image_slot_id = f"pygwalker-preview-{gid}"
        self.t_pool = ThreadPoolExecutor(1)
        try:
            self.command_app = JupyterFrontEnd()
        except Exception:
            self.command_app = None

    def init_display(self):
        display_html("", slot_id=self.image_slot_id)

    def render_gw_review(self, html: str):
        display_html(html, slot_id=self.image_slot_id)

        if self.command_app:
            try:
                self.command_app.commands.execute('docmanager:save')
            except Exception:
                pass

    def async_render_gw_review(self, html: str):
        self.t_pool.submit(self.render_gw_review, html)
