import os
import json
import time
from typing import Dict, List, Any

from jinja2 import Environment, PackageLoader

from pygwalker._constants import BYTE_LIMIT, ROOT_DIR
from pygwalker.utils.randoms import rand_str
from pygwalker.utils.display import display_html
from pygwalker import __version__, __hash__
from pygwalker_utils.config import get_config

jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)


class DataFrameEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return str(o)
        except TypeError:
            pass
        return json.JSONEncoder.default(self, o)


def gwalker_script() -> str:
    with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'pygwalker-app.iife.js'), 'r', encoding='utf8') as f:
        gwalker_js = f.read()
    return gwalker_js


def _rand_slot_id():
    return __hash__ + '-' + rand_str(6)


def _send_js(js_code: str, slot_id: str):
    display_html(
        f"""<script>(()=>{{let f=()=>{{{js_code}}};setTimeout(f,0);}})()</script>""",
        slot_id=slot_id
    )


def _send_upload_data_msg(gid: int, msg: Dict[str, Any], slot_id: str):
    msg = json.dumps(msg, cls=DataFrameEncoder)
    js_code = (
        f"document.getElementById('gwalker-{gid}')?"
        ".contentWindow?"
        f".postMessage({msg}, '*');"
    )
    _send_js(js_code, slot_id)


def get_max_limited_datas(datas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if len(datas) > 1024:
        smp0 = datas[::len(datas)//32]
        smp1 = datas[::len(datas)//37]
        avg_size = len(json.dumps(smp0, cls=DataFrameEncoder)) / len(smp0)
        avg_size = max(avg_size, len(json.dumps(smp1, cls=DataFrameEncoder)) / len(smp1))
        n = int(BYTE_LIMIT / avg_size)
        if len(datas) >= 2 * n:
            return datas[:n]
    return datas


class BatchUploadDatasTool:
    """Upload data in batches."""
    def __init__(self) -> None:
        self._caution_id = __hash__ + rand_str(6)
        self._progress_id = __hash__ + rand_str(6)

    def init(self) -> None:
        display_html("", slot_id=self._caution_id)
        display_html("", slot_id=self._progress_id)

    def run(
        self,
        *,
        data_source_id: str,
        gid: int,
        tunnel_id: str,
        records: List[Dict[str, Any]],
        sample_data_count: int,
        slot_count: int = 2
    ) -> None:
        progress_hint = "Dynamically loading into the frontend..."
        chunk = 1 << 12
        cur_slot = 0
        display_slots = [_rand_slot_id() for _ in range(slot_count)]

        tips_title = (
            f'<div id="{self._caution_id}">Dataframe is too large for ipynb files. '
            f'Only {sample_data_count} sample items are printed to the file.</div>'
        )

        display_html(tips_title, slot_id=self._caution_id)
        display_html(f"{progress_hint} {sample_data_count}/{len(records)}", slot_id=self._progress_id)

        for i in range(sample_data_count, len(records), chunk):
            data = records[i: min(i+chunk, len(records))]
            msg = {
                'action': 'postData',
                'tunnelId': tunnel_id,
                'dataSourceId': data_source_id,
                'data': data,
            }
            _send_upload_data_msg(gid, msg, display_slots[cur_slot])
            cur_slot += 1
            cur_slot %= slot_count
            display_html(f"{progress_hint} {min(i+chunk, len(records))}/{len(records)}", slot_id=self._progress_id)

        finish_msg = {
            'action': 'finishData',
            'tunnelId': tunnel_id,
            'dataSourceId': data_source_id,
        }
        time.sleep(1)
        _send_upload_data_msg(gid, finish_msg, display_slots[cur_slot])
        display_html("", slot_id=self._progress_id)
        display_html("", slot_id=self._caution_id)

        for slot_id in display_slots:
            display_html("", slot_id=slot_id)


def render_gwalker_iframe(gid: int, srcdoc: str) -> str:
    return jinja_env.get_template("pygwalker_iframe.html").render(
        gid=gid,
        srcdoc=srcdoc,
    )


def render_gwalker_html(gid: int, props: Dict) -> str:
    ds = props.get('dataSource', [])

    props['len'] = len(ds)
    walker_template = jinja_env.get_template("walk.js")
    props['version'] = __version__
    props['hashcode'] = __hash__
    if 'spec' in props:
        props['visSpec'] = props.get('spec', None)
        del props['spec']
    props['userConfig'], _ = get_config()

    props['dataSourceProps'] = {
        'tunnelId': 'tunnel!',
        'dataSourceId': f'dataSource!{rand_str(4)}',
    }

    js = walker_template.render(gwalker={'id': gid, 'props': json.dumps(props, cls=DataFrameEncoder)})
    js = "var exports={}, module={};" + gwalker_script() + js

    template = jinja_env.get_template("index.html")
    html = f"{template.render(gwalker={'id': gid, 'script': js})}"
    return html
