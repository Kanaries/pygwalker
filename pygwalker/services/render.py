import os
import json
import base64
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


def render_calc_wasm_js(use_kernel_calc: bool) -> str:
    if not use_kernel_calc:
        return """
            const initCalcWasm = async () => {};
        """.strip("\n")

    wasm_js_template = jinja_env.get_template("init_calc_wasm.js")
    wasm_exec_file_path = os.path.join(ROOT_DIR, 'templates', 'wasm_exec.js')
    wasm_file_path = os.path.join(ROOT_DIR, 'templates', 'main.wasm')

    with open(wasm_exec_file_path, 'r', encoding='utf8') as f:
        exec_wasm_js = f.read()
    with open(wasm_file_path, 'rb') as f:
        wasm_content = f.read()

    js_content = wasm_js_template.render(
        wasm_exec_js=exec_wasm_js,
        file_base64=(base64.b64encode(wasm_content)).decode(),
    )

    return js_content


def render_gwalker_html(gid: int, props: Dict) -> str:
    walker_template = jinja_env.get_template("walk.js")
    js_list = [
        "var exports={}, module={};",
        render_calc_wasm_js(props.get('useKernelCalc', False)),
        gwalker_script(),
        walker_template.render(gwalker={'id': gid, 'props': json.dumps(props, cls=DataFrameEncoder)})
    ]
    js = "\n".join(js_list)
    template = jinja_env.get_template("index.html")
    html = f"{template.render(gwalker={'id': gid, 'script': js})}"
    return html
