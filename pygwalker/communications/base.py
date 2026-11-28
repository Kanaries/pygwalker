from typing import Any, Callable, Dict, Optional
import logging

from pygwalker.communications.protocol import CommMessageRequest, CommResponse, dump_comm_response, validate_request
from pygwalker.errors import BaseError, CommProtocolError, ErrorCode

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = "Internal server error"


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

    # Whether the "open_in_desktop" endpoint may be registered for this transport. Web-framework
    # transports (Streamlit / Gradio / Reflex) serve remote users and must not expose it.
    allow_open_in_desktop: bool = True

    def __init__(self, gid: str) -> None:
        self._endpoint_map = {}
        self.gid = gid
        self._close_callback: Optional[Callable[[], Any]] = None

    def send_msg_async(self, action: str, data: Dict[str, Any]):
        raise NotImplementedError

    def set_close_callback(self, callback: Optional[Callable[[], Any]]) -> None:
        """Register a cleanup callback invoked once by ``close()``."""
        self._close_callback = callback

    def close(self) -> None:
        """Release resources tied to this communication. Safe to call repeatedly."""
        callback = getattr(self, "_close_callback", None)
        self._close_callback = None
        if callback is None:
            return
        try:
            callback()
        except Exception:
            logger.exception("Error while closing communication %s", self.gid)

    def _error_response(self, data: Any, error: Exception) -> Dict[str, Any]:
        if isinstance(error, BaseError):
            response_data = None if isinstance(error, CommProtocolError) else data
            return dump_comm_response(CommResponse(code=error.code, data=response_data, message=str(error)))
        # Never leak raw exception text (it may contain data values, SQL, paths or credentials).
        logger.exception("Unhandled error in communication handler", exc_info=error)
        return dump_comm_response(CommResponse(code=ErrorCode.UNKNOWN_ERROR, data=None, message=INTERNAL_ERROR_MESSAGE))

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
