from typing import List, Dict, Any, Optional, Union
import html as m_html
import urllib
import json

from typing_extensions import Literal
from duckdb import ParserException
import ipywidgets
import pandas as pd

from pygwalker._typing import DataFrame
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.utils.display import display_html
from pygwalker.utils.randoms import rand_str
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.render import (
    render_gwalker_html,
    render_gwalker_iframe,
    get_max_limited_datas,
)
from pygwalker.services.config import set_config
from pygwalker.services.preview_image import (
    PreviewImageTool,
    ChartData,
    render_gw_preview_html,
    render_gw_chart_preview_html
)
from pygwalker.services.upload_data import (
    BatchUploadDatasToolOnWidgets,
    BatchUploadDatasToolOnJupyter
)
from pygwalker.services.config import get_local_user_id
from pygwalker.services.spec import get_spec_json, fill_new_fields
from pygwalker.services.data_parsers import get_parser
from pygwalker.services.cloud_service import (
    write_config_to_cloud,
    get_kanaries_user_info,
    get_spec_by_text,
    upload_cloud_chart
)
from pygwalker.services.check_update import check_update
from pygwalker.services.track import track_event
from pygwalker.communications.hacker_comm import HackerCommunication, BaseCommunication
from pygwalker._constants import JUPYTER_BYTE_LIMIT, JUPYTER_WIDGETS_BYTE_LIMIT
from pygwalker import __version__


class PygWalker:
    """PygWalker"""
    def __init__(
        self,
        *,
        gid: Optional[Union[int, str]],
        dataset: Union[DataFrame, Connector, str],
        field_specs: Dict[str, Any],
        spec: str,
        source_invoke_code: str,
        hidedata_source_config: bool,
        theme_key: Literal['vega', 'g2'],
        dark: Literal['media', 'light', 'dark'],
        show_cloud_tool: bool,
        use_preview: bool,
        store_chart_data: bool,
        use_kernel_calc: bool,
        use_save_tool: bool,
        is_export_dataframe: bool,
        **kwargs
    ):
        if gid is None:
            self.gid = GlobalVarManager.get_global_gid()
        else:
            self.gid = gid
        self.data_parser = get_parser(dataset, use_kernel_calc, field_specs)
        self.origin_data_source = self.data_parser.to_records(500 if use_kernel_calc else None)
        self.field_specs = self.data_parser.raw_fields
        self.spec = spec
        self.source_invoke_code = source_invoke_code
        self.hidedata_source_config = hidedata_source_config
        self.theme_key = theme_key
        self.dark = dark
        self.data_source_id = rand_str()
        self.other_props = kwargs
        self.tunnel_id = "tunnel!"
        if GlobalVarManager.privacy == "offline":
            self.show_cloud_tool = False
        else:
            self.show_cloud_tool = show_cloud_tool
        self.use_preview = use_preview
        self.store_chart_data = store_chart_data
        self._init_spec(spec, self.field_specs)
        self.use_kernel_calc = use_kernel_calc
        self.use_save_tool = use_save_tool
        self.parse_dsl_type = "server" if isinstance(dataset, (Connector, str)) else "client"
        self.gw_mode = "explore"
        self.dataset_type = self.data_parser.dataset_tpye
        self.is_export_dataframe = is_export_dataframe
        self._last_exported_dataframe = None
        check_update()
        # Temporarily adapt to pandas import module bug
        if self.use_kernel_calc:
            try:
                self.data_parser.get_datas_by_sql("SELECT 1 FROM pygwalker_mid_table LIMIT 1")
            except Exception:
                pass

    @property
    def last_exported_dataframe(self) -> Optional[pd.DataFrame]:
        return self._last_exported_dataframe

    def _init_spec(self, spec: Dict[str, Any], field_specs: List[Dict[str, Any]]):
        spec_obj, spec_type = get_spec_json(spec)
        self._update_vis_spec(spec_obj["config"] and fill_new_fields(spec_obj["config"], field_specs))
        self.spec_type = spec_type
        self._chart_map = self._parse_chart_map_dict(spec_obj["chart_map"])
        self.spec_version = spec_obj.get("version", None)
        self.workflow_list = spec_obj.get("workflow_list", [])
        self.timezone_offset_seconds = spec_obj.get("timezoneOffsetSeconds", None)

    def _update_vis_spec(self, vis_spec: List[Dict[str, Any]]):
        self.vis_spec = vis_spec
        self._chart_name_index_map = {
            item["name"]: index
            for index, item in enumerate(vis_spec)
        }

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

    def init_streamlit_comm(self):
        """
        Initialize the communication of streamlit.
        """
        from pygwalker.communications.streamlit_comm import StreamlitCommunication

        comm = StreamlitCommunication(str(self.gid))
        self._init_callback(comm)

    def init_gradio_comm(self):
        """
        Initialize the communication of gradio.
        """
        from pygwalker.communications.gradio_comm import GradioCommunication

        comm = GradioCommunication(str(self.gid))
        self._init_callback(comm)

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
        preview_tool.render_gw_review(self._get_gw_preview_html())

    def display_preview_on_jupyter(self):
        """
        Display preview on jupyter notebook/lab.
        """
        display_html(self._get_gw_preview_html())

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
        return self._get_gw_chart_preview_html(
            chart_name,
            title="",
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
        if title is None:
            title = chart_name

        html = self._get_gw_chart_preview_html(
            chart_name,
            title=title,
            desc=desc
        )
        display_html(html)

    def _get_chart_by_name(self, chart_name: str) -> ChartData:
        if chart_name not in self._chart_map:
            raise ValueError(f"chart_name: {chart_name} not found, please confirm whether to save")
        return self._chart_map[chart_name]

    def _init_callback(self, comm: BaseCommunication, preview_tool: PreviewImageTool = None):
        upload_tool = BatchUploadDatasToolOnWidgets(comm)

        def reuqest_data_callback(_):
            upload_tool.run(
                records=self.origin_data_source,
                sample_data_count=0,
                data_source_id=self.data_source_id
            )
            return {}

        def get_latest_vis_spec(_):
            return {"visSpec": self.vis_spec}

        def save_chart_endpoint(data: Dict[str, Any]):
            chart_data = ChartData.parse_obj(data)
            self._chart_map[data["title"]] = chart_data

        def update_spec(data: Dict[str, Any]):
            spec_obj = {
                "config": data["visSpec"],
                "chart_map": {},
                "version": __version__,
                "workflow_list": data.get("workflowList", []),
                "timezoneOffsetSeconds": data.get("timezoneOffsetSeconds", None)
            }
            self._update_vis_spec(data["visSpec"])
            self.spec_version = __version__
            self.workflow_list = data.get("workflowList", [])
            self.timezone_offset_seconds = data.get("timezoneOffsetSeconds", None)

            if self.use_preview:
                preview_tool.render_gw_review(self._get_gw_preview_html())

            save_chart_endpoint(data["chartData"])
            if self.store_chart_data:
                spec_obj["chart_map"] = self._get_chart_map_dict(self._chart_map)

            if self.spec_type == "json_file":
                with open(self.spec, "w", encoding="utf-8") as f:
                    f.write(json.dumps(spec_obj))
            if self.spec_type == "json_ksf":
                write_config_to_cloud(self.spec[6:], json.dumps(spec_obj))

        def upload_spec_to_cloud(data: Dict[str, Any]):
            if data["newToken"]:
                set_config({"kanaries_token": data["newToken"]})
                GlobalVarManager.kanaries_api_key = data["newToken"]
            spec_obj = {
                "config": self.vis_spec,
                "chart_map": {},
                "version": __version__,
                "workflow_list": self.workflow_list,
                "timezoneOffsetSeconds": self.timezone_offset_seconds
            }
            file_name = data["fileName"]
            workspace_name = get_kanaries_user_info()["workspaceName"]
            path = f"{workspace_name}/{file_name}"
            write_config_to_cloud(path, json.dumps(spec_obj))
            return {"specFilePath": path}

        def _get_datas(data: Dict[str, Any]):
            sql = data["sql"]
            return {
                "datas": self.data_parser.get_datas_by_sql(
                    sql,
                    data.get("timezoneOffsetSeconds", None)
                )
            }

        def _get_datas_by_payload(data: Dict[str, Any]):
            return {
                "datas": self.data_parser.get_datas_by_payload(
                    data["payload"],
                    data.get("timezoneOffsetSeconds", None)
                )
            }

        def _get_spec_by_text(data: Dict[str, Any]):
            return {
                "data": get_spec_by_text(data["metas"], data["query"])
            }

        def _export_dataframe_by_payload(data: Dict[str, Any]):
            df = pd.DataFrame(self.data_parser.get_datas_by_payload(
                data["payload"]),
                data.get("timezoneOffsetSeconds", None)
            )
            GlobalVarManager.set_last_exported_dataframe(df)
            self._last_exported_dataframe = df

        def _export_dataframe_by_sql(data: Dict[str, Any]):
            sql = data["sql"]
            df = pd.DataFrame(self.data_parser.get_datas_by_sql(
                sql,
                data.get("timezoneOffsetSeconds", None)
            ))
            GlobalVarManager.set_last_exported_dataframe(df)
            self._last_exported_dataframe = df

        def _upload_to_cloud_charts(data: Dict[str, Any]):
            chart_id = upload_cloud_chart(
                data_parser=self.data_parser,
                chart_name=data["chartName"],
                dataset_name=data["datasetName"],
                workflow_list=data["workflowList"],
                spec_list=data["visSpec"],
                is_public=data["isPublic"],
            )
            return {"chartId": chart_id}

        comm.register("get_latest_vis_spec", get_latest_vis_spec)

        if self.use_save_tool:
            comm.register("upload_spec_to_cloud", upload_spec_to_cloud)
            comm.register("update_spec", update_spec)
            comm.register("save_chart", save_chart_endpoint)
            comm.register("request_data", reuqest_data_callback)

        if self.show_cloud_tool:
            comm.register("upload_to_cloud_charts", _upload_to_cloud_charts)
            comm.register("get_spec_by_text", _get_spec_by_text)

        if self.use_kernel_calc:
            comm.register("get_datas", _get_datas)
            comm.register("get_datas_by_payload", _get_datas_by_payload)

        if self.is_export_dataframe:
            comm.register("export_dataframe_by_payload", _export_dataframe_by_payload)
            comm.register("export_dataframe_by_sql", _export_dataframe_by_sql)

    def _send_props_track(self, props: Dict[str, Any]):
        needed_fields = {
            "id", "version", "hashcode", "hideDataSourceConfig", "themeKey",
            "dark", "env", "specType", "needLoadDatas", "showCloudTool",
            "useKernelCalc", "useSaveTool", "parseDslType", "gwMode", "datasetType"
        }
        event_info = {key: value for key, value in props.items() if key in needed_fields}
        event_info["hasKanariesToken"] = bool(GlobalVarManager.kanaries_api_key)

        track_event("invoke_props", event_info)

    def _get_props(
        self,
        env: str = "",
        data_source: Optional[Dict[str, Any]] = None,
        need_load_datas: bool = False
    ) -> Dict[str, Any]:
        if data_source is None:
            data_source = self.origin_data_source
        props = {
            "id": self.gid,
            "dataSource": data_source,
            "len": len(data_source),
            "version": __version__,
            "hashcode": get_local_user_id(),
            "userConfig": {
                "privacy": GlobalVarManager.privacy,
            },
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
            "needLoadDatas": not self.use_kernel_calc and need_load_datas,
            "showCloudTool": self.show_cloud_tool,
            "needInitChart": not (self.store_chart_data and self._chart_map),
            "useKernelCalc": self.use_kernel_calc,
            "useSaveTool": self.use_save_tool,
            "parseDslType": self.parse_dsl_type,
            "gwMode": self.gw_mode,
            "needLoadLastSpec": True,
            "datasetType": self.dataset_type,
            "extraConfig": self.other_props,
            "fieldMetas": self.data_parser.field_metas,
            "isExportDataFrame": self.is_export_dataframe,
        }

        self._send_props_track(props)

        return props

    def _get_render_iframe(self, props: Dict[str, Any], return_iframe: bool = True) -> str:
        html = render_gwalker_html(self.gid, props)
        if return_iframe:
            srcdoc = m_html.escape(html)
            return render_gwalker_iframe(self.gid, srcdoc)
        else:
            return html

    def _get_gw_preview_html(self) -> str:
        if not self.workflow_list:
            return ""
        datas = []
        for workflow in self.workflow_list:
            try:
                datas.append(self.data_parser.get_datas_by_payload(workflow, self.timezone_offset_seconds))
            except ParserException:
                datas.append([])
        html = render_gw_preview_html(
            self.vis_spec,
            datas,
            self.theme_key,
            self.gid,
            self.dark
        )

        return html

    def _get_gw_chart_preview_html(self, chart_name: int, title: str, desc: str) -> str:
        if chart_name not in self._chart_name_index_map:
            raise ValueError(f"chart_name: {chart_name} not found.")
        chart_index = self._chart_name_index_map[chart_name]

        if not self.workflow_list:
            return ""
        data = self.data_parser.get_datas_by_payload(self.workflow_list[chart_index], self.timezone_offset_seconds)
        return render_gw_chart_preview_html(
            single_vis_spec=self.vis_spec[chart_index],
            data=data,
            theme_key=self.theme_key,
            title=title,
            desc=desc,
            dark=self.dark
        )
