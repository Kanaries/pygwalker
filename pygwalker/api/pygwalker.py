from typing import List, Dict, Any, Optional, Union
import html as m_html
import urllib

from typing_extensions import Literal
import ipywidgets

from pygwalker_utils.config import get_config
from pygwalker.utils.display import display_html, display_on_streamlit
from pygwalker.utils.randoms import rand_str
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.tip_tools import TipOnStartTool
from pygwalker.services.render import (
    render_gwalker_html,
    render_gwalker_iframe,
    get_max_limited_datas
)
from pygwalker.services.preview_image import PreviewImageTool, render_preview_html
from pygwalker.services.upload_data import (
    BatchUploadDatasToolOnWidgets,
    BatchUploadDatasToolOnJupyter
)
from pygwalker.services.spec import get_spec_json
from pygwalker.communications.hacker_comm import HackerCommunication, BaseCommunication
from pygwalker._constants import JUPYTER_BYTE_LIMIT, JUPYTER_WIDGETS_BYTE_LIMIT
from pygwalker import __version__, __hash__


class PygWalker:
    """PygWalker"""
    def __init__(
        self,
        gid: Optional[Union[int, str]],
        origin_data_source: List[Dict[str, Any]],
        field_specs: Dict[str, Any],
        spec: str,
        source_invoke_code: str,
        hidedata_source_config: bool,
        theme_key: Literal['vega', 'g2'],
        dark: Literal['media', 'light', 'dark'],
        show_cloud_tool: bool,
        use_preview: bool,
        **kwargs
    ):
        if gid is None:
            self.gid = GlobalVarManager.get_global_gid()
        else:
            self.gid = gid
        self.origin_data_source = origin_data_source
        self.field_specs = field_specs
        self.spec = spec
        self.source_invoke_code = source_invoke_code
        self.hidedata_source_config = hidedata_source_config
        self.theme_key = theme_key
        self.dark = dark
        self.data_source_id = rand_str()
        self.other_props = kwargs
        self.vis_spec, self.spec_type = get_spec_json(spec)
        self.tunnel_id = "tunnel!"
        self.show_cloud_tool = show_cloud_tool
        self.use_preview = use_preview
        self._chart_map = {}

    def to_html(self) -> str:
        props = self._get_props()
        return self._get_render_iframe(props)

    def display_on_streamlit(self):
        display_on_streamlit(self.to_html())

    def display_on_jupyter(self):
        """
        Display on jupyter notebook/lab.
        If share has large data loading, only sample data can be displayed when reload.
        After that, it will be changed to python for data calculation,
        and only a small amount of data will be output to the front end to complete the analysis of big data.
        """
        data_source = get_max_limited_datas(self.origin_data_source, JUPYTER_BYTE_LIMIT)
        props = self._get_props(
            "jupyter",
            data_source,
            len(self.origin_data_source) > len(data_source)
        )
        iframe_html = self._get_render_iframe(props)

        if len(self.origin_data_source) > len(data_source):
            upload_tool = BatchUploadDatasToolOnJupyter()
            display_html(iframe_html)
            upload_tool.run(
                records=self.origin_data_source,
                sample_data_count=0,
                data_source_id=self.data_source_id,
                gid=self.gid,
                tunnel_id=self.tunnel_id,
            )
        else:
            display_html(iframe_html)

    def display_on_jupyter_use_widgets(self):
        """
        use ipywidgets, Display on jupyter notebook/lab.
        When the kernel is down, the chart will not be displayed, so use `display_on_jupyter` to share
        """
        tips_tool = TipOnStartTool(self.gid, "widgets")
        tips_tool.show()

        comm = HackerCommunication(self.gid)
        preview_tool = PreviewImageTool(self.gid)
        data_source = get_max_limited_datas(self.origin_data_source, JUPYTER_WIDGETS_BYTE_LIMIT)
        props = self._get_props(
            "jupyter_widgets",
            data_source,
            len(self.origin_data_source) > len(data_source)
        )
        iframe_html = self._get_render_iframe(props)

        html_widgets = ipywidgets.Box(
            [ipywidgets.HTML(iframe_html), comm.get_widgets()],
            layout=ipywidgets.Layout(display='block')
        )

        self._init_callback(comm, preview_tool)

        display_html(html_widgets)
        preview_tool.init_display()

    @property
    def chart_list(self) -> List[str]:
        return list(self._chart_map.keys())

    def save_chart_to_file(self, chart_name: str, path: str, save_type: Literal["html", "png"] = "png"):
        if save_type == "html":
            content = self.export_chart_html(chart_name)
            write_mode = "w"
            encoding = "utf-8"
        elif save_type == "png":
            content = self.export_chart_png(chart_name)
            write_mode = "wb"
            encoding = None
        else:
            raise ValueError(f"save_type must be html or png, but got {save_type}")

        with open(path, write_mode, encoding=encoding) as f:
            f.write(content)

    def export_chart_html(self, chart_name: str) -> str:
        chart_data = self._get_chart_by_name(chart_name)

        return render_preview_html(
            chart_data,
            f"{self.gid}-{chart_name}",
            custom_title="",
            desc=""
        )

    def export_chart_png(self, chart_name: str) -> bytes:
        chart_data = self._get_chart_by_name(chart_name)

        with urllib.request.urlopen(chart_data["singleChart"]) as png_string:
            return png_string.read()

    def display_chart(self, chart_name: str, *, title: Optional[str] = None, desc: str = ""):
        chart_data = self._get_chart_by_name(chart_name)
        html = render_preview_html(
            chart_data,
            f"{self.gid}-{chart_name}",
            custom_title=title,
            desc=desc
        )
        display_html(html)

    def _get_chart_by_name(self, chart_name: str) -> Dict[str, Any]:
        """
        datas: {
            "charts": {"rowIndex": int, ""colIndex": int, "data": str, "height": int, "width": int, "canvasHeight": int, "canvasWidth": int},
            "singleChart": str,
            "nRows": int,
            "nCols": int,
            "title": str
        }
        """
        if chart_name not in self._chart_map:
            raise ValueError(f"chart_name: {chart_name} not found, please confirm whether to save")
        return self._chart_map[chart_name]

    def _init_callback(self, comm: BaseCommunication, preview_tool: PreviewImageTool):
        upload_tool = BatchUploadDatasToolOnWidgets(comm)

        def reuqest_data_callback(_):
            upload_tool.run(
                records=self.origin_data_source,
                sample_data_count=0,
                data_source_id=self.data_source_id
            )
            return {}

        def get_latest_vis_spec(_):
            vis_spec, _ = get_spec_json(self.spec)
            return {"visSpec": vis_spec}

        def update_spec(data: Dict[str, Any]):
            with open(self.spec, "w", encoding="utf-8") as f:
                f.write(data["content"])

        def save_chart_endpoint(data: Dict[str, Any]):
            self._chart_map[data["title"]] = data
            if self.use_preview:
                preview_tool.render(data)

        comm.register("request_data", reuqest_data_callback)
        comm.register("get_latest_vis_spec", get_latest_vis_spec)
        comm.register("update_vis_spec", update_spec)
        comm.register("save_chart", save_chart_endpoint)

    def _get_props(
        self,
        env: str = "",
        data_source: Optional[Dict[str, Any]] = None,
        need_load_datas: bool = False
    ) -> Dict[str, Any]:
        if data_source is None:
            data_source = self.origin_data_source
        return {
            "id": self.gid,
            "dataSource": data_source,
            "len": len(data_source),
            "version": __version__,
            "hashcode": __hash__,
            "userConfig": get_config()[0],
            "visSpec": self.vis_spec,
            "rawFields": self.field_specs,
            "hideDataSourceConfig": self.hidedata_source_config,
            "fieldkeyGuard": False,
            "themeKey": self.theme_key,
            "dark": self.dark,
            "sourceInvokeCode": self.source_invoke_code,
            "dataSourceProps": {
                'tunnelId': self.tunnel_id,
                'dataSourceId': self.data_source_id,
            },
            "env": env,
            "specType": self.spec_type,
            "needLoadDatas": need_load_datas,
            "showCloudTool": self.show_cloud_tool,
            **self.other_props,
        }

    def _get_render_iframe(self, props: Dict[str, Any]) -> str:
        html = render_gwalker_html(self.gid, props)
        srcdoc = m_html.escape(html)
        return render_gwalker_iframe(self.gid, srcdoc)
