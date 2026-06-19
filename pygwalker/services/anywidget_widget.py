import json
from typing import Any, List, Optional

import anywidget
import traitlets

from pygwalker.communications.anywidget_comm import AnywidgetCommunication
from pygwalker.utils.frontend_assets import read_frontend_asset


class WalkerAnyWidget(anywidget.AnyWidget):
    """Anywidget shell for rendering the PyGWalker frontend."""

    _esm = read_frontend_asset("pygwalker-app.es.js", encoding="utf-8")
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
    widget.props = json.dumps(walker._get_props(env, data_source))
    comm.register_widget(widget)
    walker._init_callback(comm)
    return widget
