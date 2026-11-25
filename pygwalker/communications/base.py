from typing import Any, Callable, Dict

from pygwalker.communications.protocol import CommMessageRequest, CommResponse, dump_comm_response, validate_request
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

    def __init__(self, gid: str) -> None:
        self._endpoint_map = {}
        self.gid = gid

    def send_msg_async(self, action: str, data: Dict[str, Any]):
        raise NotImplementedError

    def _error_response(self, data: Any, error: Exception) -> Dict[str, Any]:
        if isinstance(error, BaseError):
            return dump_comm_response(CommResponse(code=error.code, data=data, message=str(error)))
        return dump_comm_response(CommResponse(code=ErrorCode.UNKNOWN_ERROR, data=data, message=str(error)))

    def _receive_msg_envelope(self, message: Any) -> Dict[str, Any]:
        try:
            request = validate_request(CommMessageRequest, message)
        except Exception as e:
            return self._error_response(None, e)

        return self._receive_msg(request.action, request.data)

    def _receive_msg(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        handler_func = self._endpoint_map.get(action, None)
        if handler_func is None:
            return dump_comm_response(
                CommResponse(code=ErrorCode.INVALID_REQUEST, data=None, message=f"Unknown action: {action}")
            )
        try:
            data = handler_func(data)
            return dump_comm_response(CommResponse(code=0, data=data, message="success"))
        except Exception as e:
            return self._error_response(data, e)

    def register(self, endpoint: str, func: Callable[[Dict[str, Any]], Any]):
        self._endpoint_map[endpoint] = func
