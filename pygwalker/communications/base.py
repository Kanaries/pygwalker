from typing import Any, Callable, Dict, Optional
import logging

from pygwalker.errors import BaseError, ErrorCode

logger = logging.getLogger(__name__)


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

    def _receive_msg(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            handler_func = self._endpoint_map.get(action)
            if handler_func is None:
                return {"code": ErrorCode.UNKNOWN_ERROR, "data": None, "message": f"Unknown action: {action}"}
            data = handler_func(data)
            return {"code": 0, "data": data, "message": "success"}
        except BaseError as e:
            return {"code": e.code, "data": data, "message": str(e)}
        except Exception:
            logger.exception("Unhandled error in communication handler")
            return {"code": ErrorCode.UNKNOWN_ERROR, "data": None, "message": "Internal server error"}

    def register(self, endpoint: str, func: Callable[[Dict[str, Any]], Any]):
        self._endpoint_map[endpoint] = func
