from typing import List, Dict, Any
from queue import Queue
from threading import Thread
import json
import logging

from pydantic import BaseModel, Field
from ipylab import JupyterFrontEnd

from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.display import display_html
from pygwalker.utils.randoms import generate_hash_code
from pygwalker.services.render import jinja_env, GWALKER_SCRIPT_BASE64, compress_data


logger = logging.getLogger(__name__)


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
    for vis_spec_item, data in zip(vis_spec_obj, datas):
        charts.append({"visSpec": vis_spec_item, "data": data})

    props = {"charts": charts, "themeKey": theme_key, "dark": appearance, "gid": gid}

    container_id = f"pygwalker-preview-{gid}"
    template = jinja_env.get_template("pygwalker_main_page.html")
    html = template.render(
        gwalker={
            "id": container_id,
            "gw_script": GWALKER_SCRIPT_BASE64,
            "component_script": "PyGWalkerApp.PreviewApp(props, gw_id);",
            "props": compress_data(json.dumps(props, cls=DataFrameEncoder)),
        },
        component_url="",
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
            "id": container_id,
            "gw_script": GWALKER_SCRIPT_BASE64,
            "component_script": "PyGWalkerApp.ChartPreviewApp(props, gw_id);",
            "props": compress_data(json.dumps(props, cls=DataFrameEncoder)),
        },
        component_url="",
    )
    return html


class PreviewImageTool:
    """Preview image tool for pygwalker"""

    def __init__(self, gid: str):
        self.gid = gid
        self.image_slot_id = f"pygwalker-preview-{gid}"
        self._render_queue: Queue[str] = Queue()
        Thread(target=self._render_queue_worker, daemon=True).start()
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
                self.command_app.commands.execute("docmanager:save")
            except Exception:
                pass

    def _render_next_preview(self):
        html = self._render_queue.get()
        try:
            self.render_gw_review(html)
        finally:
            self._render_queue.task_done()

    def _safe_render_next_preview(self):
        try:
            self._render_next_preview()
        except Exception:
            logger.exception("Failed to render pygwalker preview")

    def _render_queue_worker(self):
        while True:
            self._safe_render_next_preview()

    def async_render_gw_review(self, html: str):
        self._render_queue.put(html)
