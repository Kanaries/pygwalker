import os
import json
import base64
from typing import Dict, List, Any, Optional

from jinja2 import Environment, PackageLoader

from pygwalker._constants import ROOT_DIR
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.estimate_tools import estimate_average_data_size

jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)

with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'pygwalker-app.iife.js'), 'r', encoding='utf8') as f:
    GWALKER_SCRIPT = f.read()
    GWALKER_SCRIPT_BASE64 = base64.b64encode(GWALKER_SCRIPT.encode()).decode()


def get_max_limited_datas(datas: List[Dict[str, Any]], byte_limit: int) -> List[Dict[str, Any]]:
    if len(datas) > 1024:
        avg_size = estimate_average_data_size(datas)
        n = int(byte_limit / avg_size)
        if len(datas) >= 2 * n:
            return datas[:n]
    return datas


def render_gwalker_iframe(
    gid: int,
    srcdoc: str,
    width: Optional[str] = None,
    height: Optional[str] = None
) -> str:
    if height is None:
        height = "1010px"
    if width is None:
        width = "100%"

    return jinja_env.get_template("pygwalker_iframe.html").render(
        gid=gid,
        srcdoc=srcdoc,
        height=height,
        width=width
    )


def render_gwalker_html(gid: int, props: Dict[str, Any]) -> str:
    container_id = f"gwalker-div-{gid}"
    template = jinja_env.get_template("index.html")
    html = template.render(
        gwalker={
            'id': container_id,
            'gw_script': GWALKER_SCRIPT_BASE64,
            "component_script": "PyGWalkerApp.GWalker(props, gw_id);",
            "props": json.dumps(props, cls=DataFrameEncoder)
        }
    )
    return html
