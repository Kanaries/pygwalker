import json
import os
from typing import Any, List, Optional

import anywidget
import traitlets

from pygwalker.communications.anywidget_comm import AnywidgetCommunication
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.frontend_assets import frontend_asset_pathlib, read_frontend_asset

_TRUTHY = {"1", "true", "yes", "on"}


def _frontend_dev_mode() -> bool:
    """Whether to run the widget frontend in dev mode (load ESM from disk + enable HMR).

    Enabled by ``PYGWALKER_DEV=1`` (PyGWalker's umbrella dev flag) or anywidget's own
    ``ANYWIDGET_HMR=1``. Off by default, so normal installs keep embedding the bundled
    ESM as a string and behave exactly as before.
    """
    if os.getenv("ANYWIDGET_HMR") == "1":
        return True
    return os.getenv("PYGWALKER_DEV", "").strip().lower() in _TRUTHY


def _resolve_widget_esm() -> Any:
    """Pick the widget ESM source: a watched file Path in dev mode, else the bundled string."""
    if _frontend_dev_mode():
        # A Path lets anywidget read the built bundle from disk; with ANYWIDGET_HMR=1 it also
        # watches the file and hot-reloads the widget when `vite build --watch` rewrites it.
        os.environ.setdefault("ANYWIDGET_HMR", "1")
        return frontend_asset_pathlib("pygwalker-app.es.js")
    return read_frontend_asset("pygwalker-app.es.js", encoding="utf-8")


class WalkerAnyWidget(anywidget.AnyWidget):
    """Anywidget shell for rendering the PyGWalker frontend."""

    _esm = _resolve_widget_esm()
    props = traitlets.Unicode("").tag(sync=True)


def create_anywidget_for_walker(
    walker,
    *,
    env: str,
    data_source: Optional[List[Any]] = None,
    communication_cls=AnywidgetCommunication,
) -> WalkerAnyWidget:
    widget = WalkerAnyWidget()
    comm = communication_cls(walker.gid)
    widget.props = json.dumps(walker._get_props(env, data_source), cls=DataFrameEncoder)
    comm.register_widget(widget)
    walker._init_callback(comm)
    return widget
