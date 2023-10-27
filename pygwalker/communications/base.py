from typing import Any, Callable, Dict

from pygwalker.errors import BaseError, ErrorCode


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
    def __init__(self) -> None:
        self._endpoint_map = {}

    def send_msg_async(self, action: str, data: Dict[str, Any]):
        raise NotImplementedError

    def send_msg(self, action: str, data: Dict[str, Any]):
        raise NotImplementedError

    def _receive_msg(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        handler_func = self._endpoint_map.get(action, None)
        if handler_func is None:
            return {"code": ErrorCode.UNKNOWN_ERROR, "data": None, "message": f"Unknown action: {action}"}
        try:
            data = handler_func(data)
            return {"code": 0, "data": data, "message": "success"}
        except BaseError as e:
            return {"code": e.code, "data": data, "message": str(e)}
        except Exception as e:
            return {"code": ErrorCode.UNKNOWN_ERROR, "data": data, "message": str(e)}

    def register(self, endpoint: str, func: Callable[[Dict[str, Any]], Any]):
        self._endpoint_map[endpoint] = func
