import os
import json
import html as m_html
from typing import Dict, List, Any

from jinja2 import Environment, PackageLoader

from pygwalker._constants import ROOT_DIR
from pygwalker.utils.encode import DataFrameEncoder

jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)


def gwalker_script() -> str:
    with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'pygwalker-app.iife.js'), 'r', encoding='utf8') as f:
        gwalker_js = f.read()
    return gwalker_js


def get_max_limited_datas(datas: List[Dict[str, Any]], byte_limit: int) -> List[Dict[str, Any]]:
    if len(datas) > 1024:
        smp0 = datas[::len(datas)//32]
        smp1 = datas[::len(datas)//37]
        avg_size = len(json.dumps(smp0, cls=DataFrameEncoder)) / len(smp0)
        avg_size = max(avg_size, len(json.dumps(smp1, cls=DataFrameEncoder)) / len(smp1))
        n = int(byte_limit / avg_size)
        if len(datas) >= 2 * n:
            return datas[:n]
    return datas


def render_gwalker_iframe(gid: int, srcdoc: str) -> str:
    return jinja_env.get_template("pygwalker_iframe.html").render(
        gid=gid,
        srcdoc=srcdoc,
    )


def render_gwalker_html(gid: int, props: Dict) -> str:
    walker_template = jinja_env.get_template("walk.js")
    js = walker_template.render(gwalker={'id': gid, 'props': json.dumps(props, cls=DataFrameEncoder)})
    js = "var exports={}, module={};" + gwalker_script() + js
    template = jinja_env.get_template("index.html")
    html = f"{template.render(gwalker={'id': gid, 'script': js})}"
    return html


def render_preview_html(images: List[str], row_count: int, col_count: int, div_id: str) -> str:
    image_list = [[None] * col_count for _ in range(row_count)]
    for image in images:
        image_list[image["rowIndex"]][image["colIndex"]] = image

    with open(os.path.join(ROOT_DIR, 'templates', 'tailwind.js'), 'r', encoding='utf-8') as f:
        tailwind_js = f.read()

    html = jinja_env.get_template("preview.html").render(
        tailwind_js=tailwind_js,
        image_list=image_list,
        div_id=div_id,
    )

    iframe = jinja_env.get_template("preview_iframe.html").render(
        iframe_id=div_id,
        srcdoc=m_html.escape(html)
    )

    return iframe
