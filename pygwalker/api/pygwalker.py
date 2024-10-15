from typing import List, Dict, Any, Optional, Union
import urllib
import json

from typing_extensions import Literal
from duckdb import ParserException
import ipywidgets
import pandas as pd

from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from pygwalker.data_parsers.base import BaseDataParser, FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.utils.display import display_html
from pygwalker.utils.randoms import rand_str
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.render import (
    render_gwalker_html,
    render_gwalker_iframe,
    get_max_limited_datas,
    render_iframe_messages_html
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
from pygwalker.services.cloud_service import CloudService
from pygwalker.services.check_update import check_update
from pygwalker.services.track import track_event
from pygwalker.utils.randoms import generate_hash_code
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
        field_specs: List[FieldSpec],
        spec: str,
        source_invoke_code: str,
        theme_key: IThemeKey,
        appearance: IAppearance,
        show_cloud_tool: Optional[bool],
        use_preview: bool,
        kernel_computation: Optional[bool],
        cloud_computation: Optional[bool],
        use_save_tool: bool,
        is_export_dataframe: bool,
        kanaries_api_key: str,
        default_tab: Literal["data", "vis"],
        gw_mode: Literal["explore", "renderer", "filter_renderer", "table"],
        **kwargs
    ):
        self.kanaries_api_key = kanaries_api_key or GlobalVarManager.kanaries_api_key
        if gid is None:
            self.gid = generate_hash_code()
        else:
            self.gid = gid
        self.cloud_service = CloudService(self.kanaries_api_key)
        self.data_parser = self._get_data_parser(
            dataset=dataset,
            field_specs=field_specs,
            cloud_computation=cloud_computation,
            kanaries_api_key=self.kanaries_api_key,
            cloud_service=self.cloud_service
        )

        suggest_kernel_computation = self.data_parser.data_size > JUPYTER_BYTE_LIMIT
        self.kernel_computation = suggest_kernel_computation if kernel_computation is None else kernel_computation
        self.origin_data_source = self.data_parser.to_records(500 if self.kernel_computation else None)
        self.field_specs = self.data_parser.raw_fields
        self.spec = spec
        self.source_invoke_code = source_invoke_code
        self.theme_key = theme_key
        self.appearance = appearance
        self.data_source_id = rand_str()
        self.other_props = kwargs
        self.tunnel_id = "tunnel!"
        self.show_cloud_tool = bool(self.kanaries_api_key) if show_cloud_tool is None else show_cloud_tool
        self.use_preview = use_preview
        self._init_spec(spec, self.field_specs)
        self.use_save_tool = use_save_tool
        self.parse_dsl_type = self._get_parse_dsl_type(self.data_parser)
        self.gw_mode = gw_mode
        self.dataset_type = self.data_parser.dataset_type
        self.is_export_dataframe = is_export_dataframe
        self._last_exported_dataframe = None
        self.default_tab = default_tab
        self.cloud_computation = cloud_computation
        self.comm = None
        check_update()
        # Temporarily adapt to pandas import module bug
        if self.kernel_computation:
            try:
                self.data_parser.get_datas_by_sql("SELECT 1 FROM pygwalker_mid_table LIMIT 1")
            except Exception:
                pass
        if GlobalVarManager.privacy == "offline":
            self.show_cloud_tool = False

    @property
    def last_exported_dataframe(self) -> Optional[pd.DataFrame]:
        return self._last_exported_dataframe

    def _get_data_parser(
        self,
        *,
        dataset: Union[DataFrame, Connector, str],
        field_specs: List[FieldSpec],
        cloud_computation: bool,
        kanaries_api_key: str,
        cloud_service: CloudService
    ) -> BaseDataParser:
        data_parser = get_parser(
            dataset,
            field_specs,
            other_params={"kanaries_api_key": kanaries_api_key}
        )
        if not cloud_computation:
            return data_parser

        dataset_id = cloud_service.create_cloud_dataset(
            data_parser,
            f"temp_{rand_str()}",
            False,
            True
        )

        return get_parser(
            dataset_id,
            field_specs,
            other_params={"kanaries_api_key": kanaries_api_key}
        )

    def _get_parse_dsl_type(self, data_parser: BaseDataParser) -> Literal["server", "client"]:
        if data_parser.dataset_type.startswith("connector"):
            return "server"
        if data_parser.dataset_type == "cloud_dataset":
            return "server"
        return "client"

    def _init_spec(self, spec: Dict[str, Any], field_specs: List[FieldSpec]):
        spec_obj, spec_type = get_spec_json(spec)
        if spec_type.startswith("vega"):
            self._update_vis_spec(spec_obj["config"])
        else:
            self._update_vis_spec(spec_obj["config"] and fill_new_fields(spec_obj["config"], field_specs))
        self.spec_type = spec_type
        self._chart_map = self._parse_chart_map_dict(spec_obj["chart_map"])
        self.spec_version = spec_obj.get("version", None)
        self.workflow_list = spec_obj.get("workflow_list", [])

    def _update_vis_spec(self, vis_spec: List[Dict[str, Any]]):
        self.vis_spec = vis_spec
        self._chart_name_index_map = {
            item["name"]: index
            for index, item in enumerate(vis_spec)
            if "name" in item
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

    def to_html(self, iframe_width: Optional[str] = None, iframe_height: Optional[str] = None) -> str:
        props = self._get_props()
        return self._get_render_iframe(props, iframe_width=iframe_width, iframe_height=iframe_height)

    def to_html_without_iframe(self) -> str:
        props = self._get_props()
        html = render_gwalker_html(self.gid, props)
        return html

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
        display_html(render_iframe_messages_html(self.gid))

    def display_on_jupyter_use_widgets(self, iframe_width: Optional[str] = None, iframe_height: Optional[str] = None):
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
        iframe_html = self._get_render_iframe(props, iframe_width=iframe_width, iframe_height=iframe_height)

        html_widgets = ipywidgets.Box(
            [ipywidgets.HTML(iframe_html), comm.get_widgets()],
            layout=ipywidgets.Layout(display='block')
        )

        self._init_callback(comm, preview_tool)

        display_html(html_widgets)
        display_html(render_iframe_messages_html(self.gid))
        preview_tool.init_display()
        preview_tool.async_render_gw_review(self._get_gw_preview_html())

    def display_preview_on_jupyter(self):
        """
        Display preview on jupyter notebook/lab.
        """
        display_html(self._get_gw_preview_html(True))

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

    def get_single_chart_html_by_spec(
        self,
        *,
        spec: Dict[str, Any],
        title: str = "",
        desc: str = "",
    ) -> str:
        # pylint: disable=import-outside-toplevel
        from pygwalker.utils.dsl_transform import dsl_to_workflow
        workflow = dsl_to_workflow(spec)
        data = self.data_parser.get_datas_by_payload(workflow)
        return render_gw_chart_preview_html(
            single_vis_spec=spec,
            data=data,
            theme_key=self.theme_key,
            title=title,
            desc=desc,
            appearance=self.appearance
        )

    def _get_chart_by_name(self, chart_name: str) -> ChartData:
        if chart_name not in self._chart_map:
            raise ValueError(f"chart_name: {chart_name} not found, please confirm whether to save")
        return self._chart_map[chart_name]

    def _init_callback(self, comm: BaseCommunication, preview_tool: PreviewImageTool = None):
        upload_tool = BatchUploadDatasToolOnWidgets(comm)
        self.comm = comm

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
                "workflow_list": data.get("workflowList", [])
            }
            self._update_vis_spec(data["visSpec"])
            self.spec_version = __version__
            self.workflow_list = data.get("workflowList", [])

            if self.use_preview:
                preview_tool.async_render_gw_review(self._get_gw_preview_html())

            save_chart_endpoint(data["chartData"])

            if self.spec_type == "json_file":
                with open(self.spec, "w", encoding="utf-8") as f:
                    f.write(json.dumps(spec_obj))
            if self.spec_type == "json_ksf":
                self.cloud_service.write_config_to_cloud(self.spec[6:], json.dumps(spec_obj))

        def upload_spec_to_cloud(data: Dict[str, Any]):
            if data["newToken"]:
                set_config({"kanaries_token": data["newToken"]})
                GlobalVarManager.kanaries_api_key = data["newToken"]
            spec_obj = {
                "config": self.vis_spec,
                "chart_map": {},
                "version": __version__,
                "workflow_list": self.workflow_list,
            }
            file_name = data["fileName"]
            workspace_name = self.cloud_service.get_kanaries_user_info()["workspaceName"]
            path = f"{workspace_name}/{file_name}"
            self.cloud_service.write_config_to_cloud(path, json.dumps(spec_obj))
            return {"specFilePath": path}

        def _get_datas(data: Dict[str, Any]):
            sql = data["sql"]
            datas = self.data_parser.get_datas_by_sql(sql)
            return {
                "datas": datas
            }

        def _get_datas_by_payload(data: Dict[str, Any]):
            datas = self.data_parser.get_datas_by_payload(data["payload"])
            return {
                "datas": datas
            }

        def _batch_get_datas_by_sql(data: Dict[str, Any]):
            result = self.data_parser.batch_get_datas_by_sql(data["queryList"])
            return {
                "datas": result
            }

        def _batch_get_datas_by_payload(data: Dict[str, Any]):
            result = self.data_parser.batch_get_datas_by_payload(data["queryList"])
            return {
                "datas": result
            }

        def _get_spec_by_text(data: Dict[str, Any]):
            callback = self.other_props.get(
                "custom_ask_callback",
                self.cloud_service.get_spec_by_text
            )
            return {
                "data": callback(data["metas"], data["query"])
            }

        def _get_chart_by_chats(data: Dict[str, Any]):
            callback = self.other_props.get(
                "custom_chat_callback",
                self.cloud_service.get_chart_by_chats
            )
            return {
                "data": callback(data["metas"], data["chats"])
            }

        def _export_dataframe_by_payload(data: Dict[str, Any]):
            df = pd.DataFrame(self.data_parser.get_datas_by_payload(data["payload"]))
            GlobalVarManager.set_last_exported_dataframe(df)
            self._last_exported_dataframe = df

        def _export_dataframe_by_sql(data: Dict[str, Any]):
            sql = data["sql"]
            df = pd.DataFrame(self.data_parser.get_datas_by_sql(sql))
            GlobalVarManager.set_last_exported_dataframe(df)
            self._last_exported_dataframe = df

        def _upload_to_cloud_charts(data: Dict[str, Any]):
            result = self.cloud_service.upload_cloud_chart(
                data_parser=self.data_parser,
                chart_name=data["chartName"],
                dataset_name=data["datasetName"],
                workflow=data["workflow"],
                spec_list=data["visSpec"],
                is_public=data["isPublic"],
            )
            return {"chartId": result["chart_id"], "datasetId": result["dataset_id"]}

        def _upload_to_cloud_dashboard(data: Dict[str, Any]):
            result = self.cloud_service.upload_cloud_dashboard(
                data_parser=self.data_parser,
                dashboard_name=data["chartName"],
                dataset_name=data["datasetName"],
                workflow_list=data["workflowList"],
                spec_list=data["visSpec"],
                is_public=data["isPublic"],
                create_dashboard_flag=data["isCreateDashboard"],
                appearance=self.appearance
            )
            return {"dashboardId": result["dashboard_id"], "datasetId": result["dataset_id"]}

        comm.register("get_latest_vis_spec", get_latest_vis_spec)
        comm.register("request_data", reuqest_data_callback)
        comm.register("ping", lambda _: {})

        if self.use_save_tool:
            comm.register("upload_spec_to_cloud", upload_spec_to_cloud)
            comm.register("update_spec", update_spec)
            comm.register("save_chart", save_chart_endpoint)

        if self.show_cloud_tool:
            comm.register("upload_to_cloud_charts", _upload_to_cloud_charts)
            comm.register("upload_to_cloud_dashboard", _upload_to_cloud_dashboard)
            comm.register("get_spec_by_text", _get_spec_by_text)
            comm.register("get_chart_by_chats", _get_chart_by_chats)

        if self.kernel_computation:
            comm.register("get_datas", _get_datas)
            comm.register("get_datas_by_payload", _get_datas_by_payload)
            comm.register("batch_get_datas_by_sql", _batch_get_datas_by_sql)
            comm.register("batch_get_datas_by_payload", _batch_get_datas_by_payload)

        if self.is_export_dataframe:
            comm.register("export_dataframe_by_payload", _export_dataframe_by_payload)
            comm.register("export_dataframe_by_sql", _export_dataframe_by_sql)

    def _send_props_track(self, props: Dict[str, Any]):
        needed_fields = {
            "id", "version", "hashcode", "themeKey",
            "dark", "env", "specType", "needLoadDatas", "showCloudTool",
            "useKernelCalc", "useSaveTool", "parseDslType", "gwMode", "datasetType",
            "defaultTab", "useCloudCalc"
        }
        event_info = {key: value for key, value in props.items() if key in needed_fields}
        event_info["hasKanariesToken"] = bool(self.kanaries_api_key)

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
            "rawFields": [
                {**field, "offset": 0}
                for field in self.field_specs
            ],
            "fieldkeyGuard": False,
            "themeKey": self.theme_key,
            "dark": self.appearance,
            "sourceInvokeCode": self.source_invoke_code,
            "dataSourceProps": {
                'tunnelId': self.tunnel_id,
                'dataSourceId': self.data_source_id,
            },
            "env": env,
            "specType": self.spec_type,
            "needLoadDatas": not self.kernel_computation and need_load_datas,
            "showCloudTool": self.show_cloud_tool,
            "needInitChart": not self._chart_map,
            "useKernelCalc": self.kernel_computation,
            "useSaveTool": self.use_save_tool,
            "parseDslType": self.parse_dsl_type,
            "gwMode": self.gw_mode,
            "needLoadLastSpec": True,
            "datasetType": self.dataset_type,
            "extraConfig": self.other_props,
            "fieldMetas": self.data_parser.field_metas,
            "isExportDataFrame": self.is_export_dataframe,
            "defaultTab": self.default_tab,
            "useCloudCalc": self.cloud_computation
        }

        self._send_props_track(props)

        return props

    def _get_render_iframe(
        self,
        props: Dict[str, Any],
        return_iframe: bool = True,
        iframe_width: Optional[str] = None,
        iframe_height: Optional[str] = None
    ) -> str:
        """Get render iframe html."""
        html = render_gwalker_html(self.gid, props)
        if return_iframe:
            return render_gwalker_iframe(self.gid, html, iframe_width, iframe_height, self.appearance)
        else:
            return html

    def _get_gw_preview_html(self, manual: bool = False) -> str:
        """
        'manual' represents the user actively calling to obtain preview_html. It will randomly generate a gid, keeping it separate from the logic of walker automatically generating the preview part.
        """
        if not self.workflow_list:
            return ""
        datas = []
        for workflow in self.workflow_list:
            try:
                datas.append(self.data_parser.get_datas_by_payload(workflow))
            except ParserException:
                datas.append([])
        html = render_gw_preview_html(
            self.vis_spec,
            datas,
            self.theme_key,
            self.gid if not manual else self.gid + rand_str(),
            self.appearance
        )

        return html

    def _get_gw_chart_preview_html(self, chart_name: int, title: str, desc: str) -> str:
        if chart_name not in self._chart_name_index_map:
            raise ValueError(f"chart_name: {chart_name} not found.")
        chart_index = self._chart_name_index_map[chart_name]

        if not self.workflow_list:
            return ""
        data = self.data_parser.get_datas_by_payload(self.workflow_list[chart_index])
        return render_gw_chart_preview_html(
            single_vis_spec=self.vis_spec[chart_index],
            data=data,
            theme_key=self.theme_key,
            title=title,
            desc=desc,
            appearance=self.appearance
        )
