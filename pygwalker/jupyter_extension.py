"""On-demand kernel bridge for the PyGWalker JupyterLab companion extension.

This module is intentionally dormant.  Importing :mod:`pygwalker` does not register a
Jupyter comm target; the companion extension calls :func:`ensure_registered` in the active
kernel when the user opens its sidebar.
"""

from __future__ import annotations

import json
import keyword
import logging
import uuid
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional, Set

import pandas as pd

from pygwalker import __version__
from pygwalker.api.walker import Walker
from pygwalker.communications.base import BaseCommunication
from pygwalker.utils.encode import DataFrameEncoder


COMM_TARGET = "pygwalker.jupyter.v1"
PROTOCOL_VERSION = 1
_REGISTERED_MARKER = "_pygwalker_jupyter_v1_registered"
_LOGGER = logging.getLogger("pygwalker.jupyter_extension")


def discover_dataframes(namespace: Mapping[str, Any]) -> list[Dict[str, Any]]:
    """Return metadata for safe, top-level pandas DataFrame variables.

    Discovery deliberately reads only names, types, and ``shape``.  It never evaluates a
    client-provided expression and never serializes dataframe values.
    """

    frames = []
    for name, value in namespace.items():
        if not isinstance(name, str) or not name.isidentifier() or keyword.iskeyword(name):
            continue
        if name.startswith("_") or not isinstance(value, pd.DataFrame):
            continue
        rows, columns = value.shape
        frames.append(
            {
                "name": name,
                "rows": int(rows),
                "columns": int(columns),
            }
        )
    return sorted(frames, key=lambda frame: frame["name"].casefold())


def resolve_dataframe(namespace: Mapping[str, Any], name: str, allowed_names: Set[str]) -> pd.DataFrame:
    """Resolve a previously discovered dataframe without using ``eval``."""

    if not isinstance(name, str) or name not in allowed_names:
        raise ValueError("Refresh the sidebar and choose a discovered pandas DataFrame.")
    value = namespace.get(name)
    if not isinstance(value, pd.DataFrame):
        raise ValueError(f"'{name}' is no longer a pandas DataFrame. Refresh the sidebar.")
    return value


class JupyterExtensionCommunication(BaseCommunication):
    """Adapt an ipykernel Comm to PyGWalker's existing communication contract."""

    def __init__(self, comm: Any, gid: str = "extension") -> None:
        super().__init__(gid)
        self.comm = comm
        comm.on_msg(self._on_message)

    def send_msg_async(
        self,
        action: str,
        data: Dict[str, Any],
        rid: Optional[str] = None,
    ) -> None:
        message = {
            "gid": self.gid,
            "rid": rid or uuid.uuid4().hex,
            "action": action,
            "data": data,
        }
        self.comm.send(
            {
                "type": "pyg_response",
                "data": json.dumps(message, cls=DataFrameEncoder),
            }
        )
        _LOGGER.debug("Sent Jupyter extension comm action=%s rid=%s", action, message["rid"])

    def _on_message(self, message: Dict[str, Any]) -> None:
        content = message.get("content", {}) if isinstance(message, dict) else {}
        payload = content.get("data", {}) if isinstance(content, dict) else {}
        if not isinstance(payload, dict) or payload.get("type") != "pyg_request":
            return

        request = payload.get("msg", {})
        if not isinstance(request, dict) or request.get("action") == "finish_request":
            return

        _LOGGER.debug(
            "Received Jupyter extension comm action=%s rid=%s",
            request.get("action"),
            request.get("rid"),
        )
        response = self._receive_msg_envelope(request)
        self.send_msg_async("finish_request", response, request.get("rid"))


class JupyterExtensionSession:
    """One companion-extension connection bound to one live kernel namespace."""

    def __init__(
        self,
        comm: Any,
        namespace: MutableMapping[str, Any],
        *,
        walker_factory: Callable[..., Any] = Walker,
    ) -> None:
        self.namespace = namespace
        self.walker_factory = walker_factory
        self.communication = JupyterExtensionCommunication(comm)
        self.walker: Optional[Any] = None
        self._allowed_names: Set[str] = set()

        self.communication.register("extension_handshake", self._handshake)
        self.communication.register("list_dataframes", self._list_dataframes)
        self.communication.register("open_dataframe", self._open_dataframe)

    def _handshake(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "coreVersion": __version__,
            "capabilities": ["pandas-dataframe", "single-session", "kernel-computation"],
        }

    def _list_dataframes(self, _: Dict[str, Any]) -> Dict[str, Any]:
        dataframes = discover_dataframes(self.namespace)
        self._allowed_names = {item["name"] for item in dataframes}
        return {"dataframes": dataframes}

    def _open_dataframe(self, data: Dict[str, Any]) -> Dict[str, Any]:
        name = data.get("name")
        dataframe = resolve_dataframe(self.namespace, name, self._allowed_names)

        public_walker = self.walker_factory(
            dataframe,
            computation="kernel",
            spec_io_mode="r",
            show_cloud_tool=False,
        )
        walker = getattr(public_walker, "core", public_walker)

        # Registering on the same communication object overwrites the prior walker's endpoint
        # callbacks.  This is the explicit one-session replacement policy for Round 1.
        self.communication.gid = str(walker.gid)
        walker._init_callback(self.communication)
        self.walker = walker

        return {
            "protocolVersion": PROTOCOL_VERSION,
            "sessionId": str(walker.gid),
            "name": name,
            "props": walker._get_props(env="jupyter_extension"),
        }


def _make_target(namespace: MutableMapping[str, Any]) -> Callable[[Any, Dict[str, Any]], None]:
    def _target(comm: Any, _: Dict[str, Any]) -> None:
        # The callbacks held by ``comm`` keep the session alive for the connection lifetime.
        _LOGGER.debug("Opened Jupyter extension comm id=%s", getattr(comm, "comm_id", "unknown"))
        JupyterExtensionSession(comm, namespace)

    return _target


def ensure_registered(ipython: Optional[Any] = None) -> Dict[str, Any]:
    """Register the versioned comm target in the current IPython kernel exactly once."""

    if ipython is None:
        try:
            from IPython import get_ipython

            ipython = get_ipython()
        except Exception as exc:  # pragma: no cover - defensive import boundary
            raise RuntimeError("PyGWalker Jupyter extension requires an IPython kernel.") from exc

    kernel = getattr(ipython, "kernel", None)
    manager = getattr(kernel, "comm_manager", None)
    namespace = getattr(ipython, "user_ns", None)
    if manager is None or namespace is None:
        raise RuntimeError("PyGWalker Jupyter extension requires a live IPython kernel.")

    if not getattr(manager, _REGISTERED_MARKER, False):
        manager.register_target(COMM_TARGET, _make_target(namespace))
        setattr(manager, _REGISTERED_MARKER, True)

    return {
        "target": COMM_TARGET,
        "protocolVersion": PROTOCOL_VERSION,
        "coreVersion": __version__,
    }


__all__ = [
    "COMM_TARGET",
    "PROTOCOL_VERSION",
    "JupyterExtensionCommunication",
    "JupyterExtensionSession",
    "discover_dataframes",
    "ensure_registered",
    "resolve_dataframe",
]
