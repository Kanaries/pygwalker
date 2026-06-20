from typing import Any, Callable, Optional

import ipywidgets

from pygwalker._constants import JUPYTER_BYTE_LIMIT, JUPYTER_WIDGETS_BYTE_LIMIT
from pygwalker.communications.hacker_comm import HackerCommunication
from pygwalker.services.preview_image import PreviewImageTool
from pygwalker.services.render import get_max_limited_datas, render_iframe_messages_html
from pygwalker.services.upload_data import BatchUploadDatasToolOnJupyter


class JupyterDisplayManager:
    """Own Jupyter display flows while PygWalker keeps the public methods."""

    def __init__(self, walker, display_fn: Callable[[Any], None]):
        self.walker = walker
        self.display_fn = display_fn

    def display_on_convert_html(self) -> None:
        props = self.walker._get_props("jupyter")
        iframe_html = self.walker._get_render_iframe(props)
        self.display_fn(iframe_html)

    def display_on_jupyter(self) -> None:
        data_source = get_max_limited_datas(self.walker.origin_data_source, JUPYTER_BYTE_LIMIT)
        needs_data_upload = len(self.walker.origin_data_source) > len(data_source)
        props = self.walker._get_props("jupyter", data_source, needs_data_upload)
        iframe_html = self.walker._get_render_iframe(props)

        if needs_data_upload:
            upload_tool = BatchUploadDatasToolOnJupyter()
            self.display_fn(iframe_html)
            upload_tool.run(
                records=self.walker.origin_data_source,
                sample_data_count=0,
                data_source_id=self.walker.data_source_id,
                gid=self.walker.gid,
                tunnel_id=self.walker.tunnel_id,
            )
        else:
            self.display_fn(iframe_html)
        self.display_fn(render_iframe_messages_html(self.walker.gid))

    def display_on_jupyter_use_widgets(
        self, iframe_width: Optional[str] = None, iframe_height: Optional[str] = None
    ) -> None:
        comm = HackerCommunication(self.walker.gid)
        preview_tool = PreviewImageTool(self.walker.gid)
        data_source = get_max_limited_datas(self.walker.origin_data_source, JUPYTER_WIDGETS_BYTE_LIMIT)
        needs_data_upload = len(self.walker.origin_data_source) > len(data_source)
        props = self.walker._get_props("jupyter_widgets", data_source, needs_data_upload)
        iframe_html = self.walker._get_render_iframe(
            props,
            iframe_width=iframe_width,
            iframe_height=iframe_height,
        )

        html_widgets = ipywidgets.Box(
            [ipywidgets.HTML(iframe_html), comm.get_widgets()], layout=ipywidgets.Layout(display="block")
        )

        self.walker._init_callback(comm, preview_tool)

        self.display_fn(html_widgets)
        self.display_fn(render_iframe_messages_html(self.walker.gid))
        preview_tool.init_display()
        preview_tool.async_render_gw_review(self.walker._get_gw_preview_html())

    def display_on_jupyter_use_anywidget(self) -> None:
        from pygwalker.services.anywidget_widget import create_anywidget_for_walker

        self.walker.use_preview = False
        data_source = [] if self.walker.kernel_computation else self.walker.origin_data_source
        widget = create_anywidget_for_walker(self.walker, env="anywidget", data_source=data_source)
        self.display_fn(widget)

    def display_preview_on_jupyter(self) -> None:
        self.display_fn(self.walker._get_gw_preview_html(True))
