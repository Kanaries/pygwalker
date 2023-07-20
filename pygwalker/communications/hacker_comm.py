from threading import Lock
from typing import Any, Dict, Optional
import uuid
import json
import time

from ipywidgets import Text, Layout, Box

from .base import BaseCommunication
from pygwalker.utils.encode import DataFrameEncoder


class HackerCommunication(BaseCommunication):
    """
    Hacker communication class.
    Since it is not a long running service for multiple users,
    some expired buffers and locks will not be cleaned up.
    """
    def __init__(self, gid: str) -> None:
        super().__init__()
        self.gid = gid
        self._kernel_widget = self._get_kernel_widget()
        self._html_widget = self._get_html_widget()
        self._global_lock = Lock()
        self._send_msg_lock = Lock()
        self._lock_map = {}
        self._buffer_map = {}
        self.__increase = 0

    def send_msg(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
            This method is not available, main thread blocked widgets on_message
        """
        rid = uuid.uuid1().hex
        wait_lock = self._get_request_lock(rid)
        wait_lock.acquire(False)
        self.send_msg_async(action, data, rid=rid)
        wait_result = wait_lock.acquire(True, 15)
        if wait_result:
            wait_lock.release()
            return self._buffer_map.pop(rid, {})
        else:
            return {"success": False}

    def send_msg_async(self, action: str, data: Dict[str, Any], rid: Optional[str] = None):
        """
        To transmit messages through a widget,
        there will be problems during concurrency,
        because the timing of front-end rendering is not sure,
        so a sleep is temporarily added to solve it violently
        """
        if rid is None:
            rid = uuid.uuid1().hex
        msg = {
            "gid": self.gid,
            "rid": rid,
            "action": action,
            "data": data
        }
        with self._send_msg_lock:
            self._html_widget.value = json.dumps(msg, cls=DataFrameEncoder)
            self._html_widget.placeholder = str(self.__increase)
            self.__increase += 1
            time.sleep(0.1)

    def get_widgets(self) -> Box:
        return Box(
            children=[self._html_widget, self._kernel_widget],
            layout=Layout(display="none")
        )

    def _on_mesage(self, _):
        self.__increase += 1
        msg_json = json.loads(self._kernel_widget.value)
        action = msg_json["action"]
        data = msg_json["data"]
        rid = msg_json["rid"]

        if action == "finish_request":
            wait_lock = self._get_request_lock(rid, new=False)
            if wait_lock is None:
                return
            self._buffer_map[rid] = data
            wait_lock.release()
            self._lock_map.pop(rid, None)
        else:
            resp = self._receive_msg(action, data)
            self.send_msg_async("finish_request", resp, rid)

    def _get_html_widget(self) -> Text:
        text = Text(value="", placeholder="")
        text.add_class(f"hacker-comm-pyg-html-store-{self.gid}")
        return text

    def _get_kernel_widget(self) -> Text:
        text = Text(value="", placeholder="")
        text.add_class(f"hacker-comm-pyg-kernel-store-{self.gid}")
        text.observe(self._on_mesage, "value")
        return text

    def _get_request_lock(self, rid: str, new: bool = True) -> Optional[Lock]:
        with self._global_lock:
            if rid not in self._lock_map:
                if new:
                    self._lock_map[rid] = Lock()
                else:
                    return None
            return self._lock_map[rid]
