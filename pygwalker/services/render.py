import os
import json
import base64
import html as m_html
from typing import Dict, List, Any, Optional
import zlib

from jinja2 import Environment, PackageLoader

from pygwalker._typing import IAppearance
from pygwalker._constants import ROOT_DIR
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.estimate_tools import estimate_average_data_size
from pygwalker.services.global_var import GlobalVarManager

jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)


def compress_data(data: str) -> str:
    compress = zlib.compressobj(zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, 15, 8, 0)
    compressed_data = compress.compress(data.encode())
    compressed_data += compress.flush()
    return base64.b64encode(compressed_data).decode()


with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'pygwalker-app.iife.js'), 'r', encoding='utf8') as f:
    GWALKER_SCRIPT = f.read()
    GWALKER_SCRIPT_BASE64 = compress_data(GWALKER_SCRIPT)


def get_max_limited_datas(datas: List[Dict[str, Any]], byte_limit: int) -> List[Dict[str, Any]]:
    if len(datas) > 1024:
        avg_size = estimate_average_data_size(datas)
        n = int(byte_limit / avg_size)
        if len(datas) >= 2 * n:
            return datas[:n]
    return datas


def render_iframe_messages_html(gid: str) -> str:
    return jinja_env.get_template("jupyter_iframe_message.html").render(gid=gid)


def render_gwalker_iframe(
    gid: int,
    html: str,
    width: Optional[str] = None,
    height: Optional[str] = None,
    appearance: IAppearance = "media",
) -> str:
    if height is None:
        height = "960px"
    if width is None:
        width = "100%"

    return jinja_env.get_template("pygwalker_iframe.html").render(
        gid=gid,
        srcdoc=m_html.escape(html),
        height=height,
        width=width,
        appearance=appearance,
        component_url=GlobalVarManager.component_url
    )


def render_gwalker_html(gid: int, props: Dict[str, Any]) -> str:
    container_id = f"gwalker-div-{gid}"
    template = jinja_env.get_template("pygwalker_main_page.html")
    html = template.render(
        gwalker={
            'id': container_id,
            'gw_script': GWALKER_SCRIPT_BASE64,
            "component_script": "PyGWalkerApp.GWalker(props, gw_id);",
            "props": compress_data(json.dumps(props, cls=DataFrameEncoder)),
        },
        component_url=GlobalVarManager.component_url
    )
    return html
