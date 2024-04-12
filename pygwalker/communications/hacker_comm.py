from threading import Lock
from typing import Any, Dict, Optional, List
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
        super().__init__(gid)
        self._kernel_widget = self._get_kernel_widget()
        self._html_widget = self._get_html_widget()
        self._send_msg_lock = Lock()
        self.__increase = 0

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
            children=[self._html_widget, *self._kernel_widget],
            layout=Layout(display="none")
        )

    def _on_mesage(self, info: Dict[str, Any]):
        self.__increase += 1
        msg_json = json.loads(info["new"])
        action = msg_json["action"]
        data = msg_json["data"]
        rid = msg_json["rid"]

        if action == "finish_request":
            return

        resp = self._receive_msg(action, data)
        self.send_msg_async("finish_request", resp, rid)

    def _get_html_widget(self) -> Text:
        text = Text(value="", placeholder="")
        text.add_class(f"hacker-comm-pyg-html-store-{self.gid}")
        return text

    def _get_kernel_widget(self) -> List[Text]:
        text_list = []
        for index in range(5):
            text = Text(value="", placeholder="")
            text.add_class(f"hacker-comm-pyg-kernel-store-{self.gid}-{index}")
            text.observe(self._on_mesage, "value")
            text_list.append(text)
        return text_list
