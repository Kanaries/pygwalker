from typing import Any, Callable, Dict

from pygwalker.communications.protocol import CommMessageRequest, validate_request
from pygwalker.errors import BaseError, CommProtocolError, ErrorCode
from pygwalker.services.track import track_event


def _upload_error_info(gid: str, action: str, error: Exception):
    if isinstance(error, CommProtocolError):
        return
    try:
        track_event(
            "pygwalker_error", {"gid": gid, "action": action, "error": str(error), "error_type": type(error).__name__}
        )
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

    def _error_response(self, action: str, data: Any, error: Exception) -> Dict[str, Any]:
        if isinstance(error, BaseError):
            _upload_error_info(self.gid, action, error)
            return {"code": error.code, "data": data, "message": str(error)}

        _upload_error_info(self.gid, action, error)
        return {"code": ErrorCode.UNKNOWN_ERROR, "data": data, "message": str(error)}

    def _receive_msg_envelope(self, message: Any) -> Dict[str, Any]:
        try:
            request = validate_request(CommMessageRequest, message)
        except BaseError as e:
            return self._error_response("", None, e)
        except Exception as e:
            return self._error_response("", None, e)

        return self._receive_msg(request.action, request.data)

    def _receive_msg(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        handler_func = self._endpoint_map.get(action, None)
        if handler_func is None:
            return {"code": ErrorCode.UNKNOWN_ERROR, "data": None, "message": f"Unknown action: {action}"}
        try:
            data = handler_func(data)
            return {"code": 0, "data": data, "message": "success"}
        except BaseError as e:
            return self._error_response(action, data, e)
        except Exception as e:
            return self._error_response(action, data, e)

    def register(self, endpoint: str, func: Callable[[Dict[str, Any]], Any]):
        self._endpoint_map[endpoint] = func
