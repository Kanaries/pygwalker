from typing import Any, Dict, Optional, List
import uuid
import json

import anywidget

from .base import BaseCommunication
from pygwalker.utils.encode import DataFrameEncoder


class AnywidgetCommunication(BaseCommunication):
    """communication class for anywidget"""
    def register_widget(self, widget: anywidget.AnyWidget) -> None:
        """register widget"""
        self.widget = widget
        self.widget.on_msg(self._on_mesage)

    def send_msg_async(self, action: str, data: Dict[str, Any], rid: Optional[str] = None):
        """send message base on anywidget"""
        if rid is None:
            rid = uuid.uuid1().hex
        msg = {
            "gid": self.gid,
            "rid": rid,
            "action": action,
            "data": data
        }
        self.widget.send({"type": "pyg_response", "data": json.dumps(msg, cls=DataFrameEncoder)})

    def _on_mesage(self, _: anywidget.AnyWidget, data: Dict[str, Any], buffers: List[Any]):
        if data.get("type", "") != "pyg_request":
            return
        
        msg = data["msg"]
        action = msg["action"]
        rid = msg["rid"]

        if action == "finish_request":
            return

        resp = self._receive_msg(action, msg["data"])
        self.send_msg_async("finish_request", resp, rid)
