from typing import Any, Callable, Dict

from pygwalker.errors import BaseError, ErrorCode
from pygwalker.services.track import track_event


def _upload_error_info(gid: str, action: str, error: Exception):
    try:
        track_event("pygwalker_error", {
            "gid": gid,
            "action": action,
            "error": str(error),
            "error_type": type(error).__name__
        })
    except Exception:
        pass


class BaseCommunication:
    """
    Base class for communication
    message format:
    {
        "rid": "xxx",
        "action": "xxx",
        "data": {}
    }
    """
    def __init__(self, gid: str) -> None:
        self._endpoint_map = {}
        self.gid = gid

    def send_msg_async(self, action: str, data: Dict[str, Any]):
        raise NotImplementedError

    def _receive_msg(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        handler_func = self._endpoint_map.get(action, None)
        if handler_func is None:
            return {"code": ErrorCode.UNKNOWN_ERROR, "data": None, "message": f"Unknown action: {action}"}
        try:
            data = handler_func(data)
            return {"code": 0, "data": data, "message": "success"}
        except BaseError as e:
            _upload_error_info(self.gid, action, e)
            return {"code": e.code, "data": data, "message": str(e)}
        except Exception as e:
            _upload_error_info(self.gid, action, e)
            return {"code": ErrorCode.UNKNOWN_ERROR, "data": data, "message": str(e)}

    def register(self, endpoint: str, func: Callable[[Dict[str, Any]], Any]):
        self._endpoint_map[endpoint] = func
