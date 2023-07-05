import os
import json
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
