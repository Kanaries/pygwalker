from typing import Dict, Any, List
import time
import json
import html as m_html

from pygwalker.utils.randoms import rand_str
from pygwalker.utils.display import display_html
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.communications.base import BaseCommunication
from pygwalker import __hash__


def _send_js(js_code: str, slot_id: str):
    display_html(
        f"""<style onload="(()=>{{let f=()=>{{{m_html.escape(js_code)}}};setTimeout(f,0);}})();" />""",
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
        chunk = 1 << 12
        cur_slot = 0
        display_slots = [_rand_slot_id() for _ in range(slot_count)]

        time.sleep(1)
        for i in range(sample_data_count, len(records), chunk):
            data = records[i: min(i+chunk, len(records))]
            msg = {
                'action': 'postData',
                'tunnelId': tunnel_id,
                'dataSourceId': data_source_id,
                'data': data,
                "total": len(records),
                "curIndex": i,
            }
            _send_upload_data_msg(gid, msg, display_slots[cur_slot])
            cur_slot += 1
            cur_slot %= slot_count

        finish_msg = {
            'action': 'finishData',
            'tunnelId': tunnel_id,
            'dataSourceId': data_source_id,
        }
        time.sleep(1)
        _send_upload_data_msg(gid, finish_msg, display_slots[cur_slot])

        for slot_id in display_slots:
            display_html("", slot_id=slot_id)


class BatchUploadDatasToolOnWidgets:
    """Upload data in batches(use ipywidgets)"""
    def __init__(self, comm: BaseCommunication) -> None:
        self.comm = comm

    def run(
        self,
        *,
        data_source_id: str,
        records: List[Dict[str, Any]],
        sample_data_count: int
    ) -> None:
        chunk = 1 << 12

        for i in range(sample_data_count, len(records), chunk):
            data = records[i: min(i+chunk, len(records))]
            msg = {
                'dataSourceId': data_source_id,
                "total": len(records),
                "curIndex": i,
                'data': data,
            }
            self.comm.send_msg_async("postData", msg)

        finish_msg = {
            'dataSourceId': data_source_id,
        }
        time.sleep(0.1)
        self.comm.send_msg_async("finishData", finish_msg)
