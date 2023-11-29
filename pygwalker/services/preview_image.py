from typing import Optional, List, Dict, Any
import base64
import zlib
import json

from pydantic import BaseModel, Field

from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.display import display_html
from pygwalker.utils.randoms import generate_hash_code
from pygwalker.services.render import jinja_env, gwalker_script


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


def _compress_data(data: List[List[Dict[str, Any]]]) -> str:
    formated_data = {}
    if data:
        keys = list(data[0].keys())
        formated_data = {key: [] for key in keys}
        for item in data:
            for key in keys:
                formated_data[key].append(item[key])

    data_json_str = json.dumps(formated_data, cls=DataFrameEncoder)
    data_base64_str = base64.b64encode(zlib.compress(data_json_str.encode())).decode()
    return data_base64_str


def render_preview_html(
    chart_data: ChartData,
    div_id: str,
    *,
    custom_title: Optional[str] = None,
    desc: str = "",
) -> str:
    image_list = [[None] * chart_data.n_cols for _ in range(chart_data.n_rows)]
    for image in chart_data.charts:
        image_list[image.row_index][image.col_index] = image

    html = jinja_env.get_template("preview.html").render(
        image_list=image_list,
        div_id=div_id,
        title=custom_title if custom_title is not None else chart_data.title,
        desc=desc,
    )

    return html


def render_preview_html_for_multi_charts(charts_map: Dict[str, ChartData], gid: str, preview_id: str) -> str:
    tab_name = "tab-pyg-" + str(gid)
    items = []
    for chart_data in charts_map.values():
        div_id = f"{gid}-{chart_data.title}".replace(" ", "")
        chart_html = render_preview_html(chart_data, div_id, custom_title="")
        items.append({
            "tab_id": "tab-" + div_id,
            "chart_title": chart_data.title,
            "chart_html": chart_html
        })

    html = jinja_env.get_template("preview_list.html").render(
        tab_name=tab_name,
        preview_id=preview_id,
        items=items
    )

    return html


def render_gw_preview_html(
    vis_spec_obj: List[Dict[str, Any]],
    datas: List[List[Dict[str, Any]]],
    theme_key: str,
    gid: str
) -> str:
    """
    Render html for previewing gwalker(use purerenderer mode of graphic-wlaker, not png preview)
    """
    charts = []
    for vis_spec_item, data in zip(
        vis_spec_obj,
        datas
    ):
        data_base64_str = _compress_data(data)
        charts.append({
            "visSpec": vis_spec_item,
            "data": data_base64_str
        })

    props = {"charts": charts, "themeKey": theme_key}

    preview_template = jinja_env.get_template("gw_preview.js")
    container_id = f"pygwalker-preview-{gid}"
    js_list = [
        gwalker_script(),
        preview_template.render(gwalker={'id': container_id, 'props': json.dumps(props)})
    ]
    js = "\n".join(js_list)
    template = jinja_env.get_template("index.html")
    html = f"{template.render(gwalker={'id': container_id, 'script': js})}"
    return html


def render_gw_chart_preview_html(
    *,
    single_vis_spec: Dict[str, Any],
    data: List[Dict[str, Any]],
    theme_key: str,
    title: str,
    desc: str,
) -> str:
    """
    Render html for single chart(use purerenderer mode of graphic-wlaker, not png preview)
    """

    props = {
        "visSpec": single_vis_spec,
        "data": _compress_data(data),
        "themeKey": theme_key,
        "title": title,
        "desc": desc,
    }

    chart_preview_template = jinja_env.get_template("gw_chart_preview.js")
    container_id = f"pygwalker-chart-preview-{generate_hash_code()[:20]}"
    js_list = [
        gwalker_script(),
        chart_preview_template.render(gwalker={'id': container_id, 'props': json.dumps(props)})
    ]
    js = "\n".join(js_list)
    template = jinja_env.get_template("index.html")
    html = f"{template.render(gwalker={'id': container_id, 'script': js})}"
    return html


class PreviewImageTool:
    """Preview image tool for pygwalker"""
    def __init__(self, gid: str):
        self.gid = gid
        self.image_slot_id = f"pygwalker-preview-{gid}"

    def init_display(self):
        display_html("", slot_id=self.image_slot_id)

    def render(self, charts_map: Dict[str, ChartData]):
        html = render_preview_html_for_multi_charts(charts_map, self.gid, self.image_slot_id)
        display_html(html, slot_id=self.image_slot_id)

    def render_gw_review(self, html: str):
        display_html(html, slot_id=self.image_slot_id)
