from typing import Dict, Any, List
import time
import json

from pygwalker.utils.randoms import rand_str
from pygwalker.utils.display import display_html
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker import __hash__


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


def _rand_slot_id():
    return __hash__ + '-' + rand_str(6)


class BatchUploadDatasToolOnJupyter:
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
