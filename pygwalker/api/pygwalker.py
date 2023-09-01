from typing import List, Dict, Any, Optional, Union
import html as m_html
import urllib
import json

from typing_extensions import Literal
import ipywidgets

from pygwalker_utils.config import get_config
from pygwalker._typing import DataFrame
from pygwalker.utils.display import display_html, display_on_streamlit
from pygwalker.utils.randoms import rand_str
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.render import (
    render_gwalker_html,
    render_gwalker_iframe,
    get_max_limited_datas,
    get_dsl_wasm
)
from pygwalker.services.preview_image import PreviewImageTool, render_preview_html, ChartData
from pygwalker.services.upload_data import (
    BatchUploadDatasToolOnWidgets,
    BatchUploadDatasToolOnJupyter
)
from pygwalker.services.spec import get_spec_json, fill_new_fields
from pygwalker.services.data_parsers import get_parser
from pygwalker.services.cloud_service import create_shared_chart
from pygwalker.communications.hacker_comm import HackerCommunication, BaseCommunication
from pygwalker.errors import CloudFunctionError, CsvFileTooLargeError
from pygwalker._constants import JUPYTER_BYTE_LIMIT, JUPYTER_WIDGETS_BYTE_LIMIT
from pygwalker import __version__, __hash__


class PygWalker:
    """PygWalker"""
    def __init__(
        self,
        gid: Optional[Union[int, str]],
        df: DataFrame,
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
        **kwargs
    ):
        if gid is None:
            self.gid = GlobalVarManager.get_global_gid()
        else:
            self.gid = gid
        self.df_parser = get_parser(df, use_kernel_calc)
        self.origin_data_source = self.df_parser.to_records(500 if use_kernel_calc else None)
        self.field_specs = self.df_parser.raw_fields(field_specs=field_specs)
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
        self._init_spec(spec, self.field_specs)
        self.use_kernel_calc = use_kernel_calc

    def _init_spec(self, spec: Dict[str, Any], field_specs: List[Dict[str, Any]]):
        spec_obj, spec_type = get_spec_json(spec)
        self.vis_spec = spec_obj["config"] and fill_new_fields(spec_obj["config"], field_specs)
        self.spec_type = spec_type
        self._chart_map = self._parse_chart_map_dict(spec_obj["chart_map"])
        self.spec_version = spec_obj.get("version", None)

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

    def _upload_charts_to_could(self, name: str, new_notebook: bool, chart: ChartData) -> str:
        """upload charts config and datas to kanaries cloud"""
        fid_list = [field["fid"] for field in self.field_specs]
        meta = {
            "dataSources": [{
                "id": "dataSource-0",
                "data": []
            }],
            "datasets": [{
                "id": 'dataset-0',
                "name": 'DataSet',
                "rawFields": self.field_specs,
                "dsId": 'dataSource-0',
            }],
            "specList": json.loads(self.vis_spec)
        }

        chart_base64 = chart.single_chart.split(",")[1]
        dataset_content = self.df_parser.to_csv()
        if dataset_content.__sizeof__() > 100 * 1024 * 1024:
            raise CsvFileTooLargeError("dataset too large(>100MB), currently unable to upload, the next version will optimize it.")
        return create_shared_chart(
            chart_name=name,
            dataset_content=dataset_content,
            fid_list=fid_list,
            meta=json.dumps(meta),
            new_notebook=new_notebook,
            thumbnail=chart_base64
        )

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
            return {"visSpec": self.vis_spec}

        def save_chart_endpoint(data: Dict[str, Any]):
            chart_data = ChartData.parse_obj(data)
            self._chart_map[data["title"]] = chart_data
            if self.use_preview:
                preview_tool.render(self._chart_map)

        def update_spec(data: Dict[str, Any]):
            spec_obj = {"config": data["visSpec"], "chart_map": {}, "version": __version__}
            self.vis_spec = data["visSpec"]
            save_chart_endpoint(data["chartData"])
            if self.store_chart_data:
                spec_obj["chart_map"] = self._get_chart_map_dict(self._chart_map)

            with open(self.spec, "w", encoding="utf-8") as f:
                f.write(json.dumps(spec_obj))

        def upload_charts(data: Dict[str, Any]):
            if not GlobalVarManager.kanaries_api_key:
                raise CloudFunctionError("no_kanaries_api_key")
            self.vis_spec = data["visSpec"]
            chart_data = ChartData.parse_obj(data["chartData"])
            share_url = self._upload_charts_to_could(
                data["chartName"],
                data["newNotebook"],
                chart_data
            )
            return {"shareUrl": share_url}

        comm.register("request_data", reuqest_data_callback)
        comm.register("get_latest_vis_spec", get_latest_vis_spec)
        comm.register("update_spec", update_spec)
        comm.register("save_chart", save_chart_endpoint)
        comm.register("upload_charts", upload_charts)

        if self.use_kernel_calc:
            def _get_datas(data: Dict[str, Any]):
                sql = data["sql"].encode('utf-8').decode('unicode_escape')
                return {
                    "datas": self.df_parser.get_datas_by_sql(sql)
                }
            comm.register("get_datas", _get_datas)

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
            "needLoadDatas": not self.use_kernel_calc and need_load_datas,
            "showCloudTool": self.show_cloud_tool,
            "needInitChart": not (self.store_chart_data and self._chart_map),
            "useKernelCalc": self.use_kernel_calc,
            "dslToSqlWasmContent": get_dsl_wasm() if self.use_kernel_calc else "",
            **self.other_props,
        }

    def _get_render_iframe(self, props: Dict[str, Any]) -> str:
        html = render_gwalker_html(self.gid, props)
        srcdoc = m_html.escape(html)
        return render_gwalker_iframe(self.gid, srcdoc)
