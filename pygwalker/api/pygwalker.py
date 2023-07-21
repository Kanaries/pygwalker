from typing import List, Dict, Any, Optional, Union
import html as m_html
import urllib
import json

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
from pygwalker.services.preview_image import PreviewImageTool, render_preview_html, ChartData
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
        store_chart_data: bool,
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
        self.tunnel_id = "tunnel!"
        self.show_cloud_tool = show_cloud_tool
        self.use_preview = use_preview
        self.store_chart_data = store_chart_data
        self._init_spec(spec)

    def _init_spec(self, spec: Dict[str, Any]):
        spec_obj, spec_type = get_spec_json(spec)
        self.vis_spec = spec_obj["config"]
        self.spec_type = spec_type
        self._chart_map = self._parse_chart_map_dict(spec_obj["chart_map"])

    def _get_chart_map_dict(self, chart_map: Dict[str, ChartData]) -> Dict[str, Any]:
        return {
            key: value.dict(by_alias=True)
            for key, value in chart_map.items()
        }

    def _parse_chart_map_dict(self, chart_map_dict: Dict[str, Any]) -> Dict[str, ChartData]:
        return {
            key: ChartData.parse_obj(value)
            for key, value in chart_map_dict.items()
        }

    def to_html(self) -> str:
        props = self._get_props()
        return self._get_render_iframe(props)

    def to_html_without_iframe(self) -> str:
        props = self._get_props()
        html = render_gwalker_html(self.gid, props)
        return html

    def display_on_streamlit(self):
        display_on_streamlit(self.to_html())

    def display_on_convert_html(self):
        """
        Display on jupyter-nbconvert html.
        """
        props = self._get_props("jupyter")
        iframe_html = self._get_render_iframe(props)
        display_html(iframe_html)

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
        preview_tool.render(self._chart_map)

    @property
    def chart_list(self) -> List[str]:
        """
        Get the list of saved charts.
        """
        return list(self._chart_map.keys())

    def save_chart_to_file(self, chart_name: str, path: str, save_type: Literal["html", "png"] = "png"):
        """
        Save the chart to a file.
        """
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
        """
        Export the chart as a html string.
        """
        chart_data = self._get_chart_by_name(chart_name)

        return render_preview_html(
            chart_data,
            f"{self.gid}-{chart_name}",
            custom_title="",
            desc=""
        )

    def export_chart_png(self, chart_name: str) -> bytes:
        """
        Export the chart as a png bytes.
        """
        chart_data = self._get_chart_by_name(chart_name)

        with urllib.request.urlopen(chart_data.single_chart) as png_string:
            return png_string.read()

    def display_chart(self, chart_name: str, *, title: Optional[str] = None, desc: str = ""):
        """
        Display the chart in the notebook.
        """
        chart_data = self._get_chart_by_name(chart_name)
        html = render_preview_html(
            chart_data,
            f"{self.gid}-{chart_name}",
            custom_title=title,
            desc=desc
        )
        display_html(html)

    def _get_chart_by_name(self, chart_name: str) -> ChartData:
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
            spec_obj, _ = get_spec_json(self.spec)
            return {"visSpec": spec_obj["config"]}

        def save_chart_endpoint(data: Dict[str, Any]):
            chart_data = ChartData.parse_obj(data)
            self._chart_map[data["title"]] = chart_data
            if self.use_preview:
                preview_tool.render(self._chart_map)

        def update_spec(data: Dict[str, Any]):
            spec_obj = {"config": data["visSpec"], "chart_map": {}}
            save_chart_endpoint(data["chartData"])
            if self.store_chart_data:
                spec_obj["chart_map"] = self._get_chart_map_dict(self._chart_map)

            with open(self.spec, "w", encoding="utf-8") as f:
                f.write(json.dumps(spec_obj))

        comm.register("request_data", reuqest_data_callback)
        comm.register("get_latest_vis_spec", get_latest_vis_spec)
        comm.register("update_spec", update_spec)
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
            "needInitChart": not (self.store_chart_data and self._chart_map),
            **self.other_props,
        }

    def _get_render_iframe(self, props: Dict[str, Any]) -> str:
        html = render_gwalker_html(self.gid, props)
        srcdoc = m_html.escape(html)
        return render_gwalker_iframe(self.gid, srcdoc)
