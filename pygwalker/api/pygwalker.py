from typing import List, Dict, Any, Optional, Union
import json
import keyword
import warnings

from typing_extensions import Literal
import pandas as pd

from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from pygwalker.data_parsers.base import BaseDataParser, FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.utils.display import display_html
from pygwalker.utils.randoms import rand_str
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.preview_image import (
    PreviewImageTool,
    ChartData,
)
from pygwalker.services.chart_export import ChartExportManager
from pygwalker.services.upload_data import BatchUploadDatasToolOnWidgets
from pygwalker.services.config import get_local_user_id
from pygwalker.services.comm_handler import CommHandler
from pygwalker.services.data_bridge import DataBridge
from pygwalker.services.jupyter_display import JupyterDisplayManager
from pygwalker.services.props_builder import PropsBuilder
from pygwalker.services.props_tracker import PropsTracker
from pygwalker.services.render_manager import RenderManager
from pygwalker.services.spec_manager import SpecManager
from pygwalker.services.cloud_service import CloudService
from pygwalker.services.check_update import check_update
from pygwalker.services.track import track_event
from pygwalker.utils.randoms import generate_hash_code
from pygwalker.communications.hacker_comm import BaseCommunication


def _warn_legacy_jupyter_transport(entrypoint: str) -> None:
    warnings.warn(
        f"`{entrypoint}` uses a legacy Jupyter transport and is deprecated. "
        "Use `display_on_jupyter_use_anywidget()` or the default `Walker.show()`/`pyg.walk()` anywidget path.",
        DeprecationWarning,
        stacklevel=3,
    )


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
        **kwargs,
    ):
        self.kanaries_api_key = kanaries_api_key or GlobalVarManager.kanaries_api_key
        if gid is None:
            self.gid = generate_hash_code()
        else:
            self.gid = gid
        self.cloud_service = CloudService(self.kanaries_api_key)
        self.data_bridge = DataBridge(
            dataset=dataset,
            field_specs=field_specs,
            cloud_computation=cloud_computation,
            kernel_computation=kernel_computation,
            kanaries_api_key=self.kanaries_api_key,
            cloud_service=self.cloud_service,
            parser_factory=self._get_data_parser,
        )
        self.spec = spec
        self.source_invoke_code = source_invoke_code
        self.theme_key = theme_key
        self.appearance = appearance
        self.data_source_id = rand_str()
        self.other_props = kwargs
        self.tunnel_id = "tunnel!"
        self.show_cloud_tool = bool(self.kanaries_api_key) if show_cloud_tool is None else show_cloud_tool
        self.use_preview = use_preview
        self.spec_manager = SpecManager(spec, self.field_specs)
        self.use_save_tool = use_save_tool
        self.gw_mode = gw_mode
        self.is_export_dataframe = is_export_dataframe
        self._last_exported_dataframe = None
        self.default_tab = default_tab
        self.cloud_computation = cloud_computation
        self.comm = None
        self.props_builder = PropsBuilder(self, lambda: get_local_user_id())
        self.props_tracker = PropsTracker(self, lambda event, props: track_event(event, props))
        self.render_manager = RenderManager(self)
        self.jupyter_display_manager = JupyterDisplayManager(self, lambda content: display_html(content))
        self.chart_export_manager = ChartExportManager(self, lambda content: display_html(content))
        check_update()
        # Temporarily adapt to pandas import module bug
        if self.kernel_computation:
            self.data_bridge.warm_kernel_table()
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
        cloud_service: CloudService,
    ) -> BaseDataParser:
        return DataBridge.create_data_parser(
            dataset=dataset,
            field_specs=field_specs,
            cloud_computation=cloud_computation,
            kanaries_api_key=kanaries_api_key,
            cloud_service=cloud_service,
        )

    def _get_parse_dsl_type(self, data_parser: BaseDataParser) -> Literal["server", "client"]:
        return DataBridge.get_parse_dsl_type(data_parser)

    @property
    def data_parser(self) -> BaseDataParser:
        return self.data_bridge.data_parser

    @data_parser.setter
    def data_parser(self, value: BaseDataParser):
        self.data_bridge.data_parser = value

    @property
    def kernel_computation(self) -> bool:
        return self.data_bridge.kernel_computation

    @kernel_computation.setter
    def kernel_computation(self, value: bool):
        self.data_bridge.kernel_computation = value

    @property
    def origin_data_source(self) -> List[Dict[str, Any]]:
        return self.data_bridge.origin_data_source

    @origin_data_source.setter
    def origin_data_source(self, value: List[Dict[str, Any]]):
        self.data_bridge.origin_data_source = value

    @property
    def field_specs(self) -> List[Dict[str, Any]]:
        return self.data_bridge.field_specs

    @field_specs.setter
    def field_specs(self, value: List[Dict[str, Any]]):
        self.data_bridge.field_specs = value

    @property
    def parse_dsl_type(self) -> Literal["server", "client"]:
        return self.data_bridge.parse_dsl_type

    @parse_dsl_type.setter
    def parse_dsl_type(self, value: Literal["server", "client"]):
        self.data_bridge.parse_dsl_type = value

    @property
    def dataset_type(self) -> str:
        return self.data_bridge.dataset_type

    @dataset_type.setter
    def dataset_type(self, value: str):
        self.data_bridge.dataset_type = value

    @property
    def spec_type(self) -> str:
        return self.spec_manager.spec_type

    @spec_type.setter
    def spec_type(self, value: str):
        self.spec_manager.spec_type = value

    @property
    def spec_version(self):
        return self.spec_manager.spec_version

    @spec_version.setter
    def spec_version(self, value):
        self.spec_manager.spec_version = value

    @property
    def vis_spec(self) -> List[Dict[str, Any]]:
        return self.spec_manager.vis_spec

    @vis_spec.setter
    def vis_spec(self, value: List[Dict[str, Any]]):
        self.spec_manager.update_vis_spec(value)

    @property
    def workflow_list(self) -> List[Dict[str, Any]]:
        return self.spec_manager.workflow_list

    @workflow_list.setter
    def workflow_list(self, value: List[Dict[str, Any]]):
        self.spec_manager.workflow_list = value

    @property
    def _chart_map(self):
        return self.spec_manager.chart_map

    @_chart_map.setter
    def _chart_map(self, value):
        self.spec_manager.chart_map = value

    @property
    def _chart_name_index_map(self):
        return self.spec_manager.chart_name_index_map

    @_chart_name_index_map.setter
    def _chart_name_index_map(self, value):
        self.spec_manager.chart_name_index_map = value

    def to_html(self, iframe_width: Optional[str] = None, iframe_height: Optional[str] = None) -> str:
        props = self._get_props()
        return self._get_render_iframe(props, iframe_width=iframe_width, iframe_height=iframe_height)

    def to_html_without_iframe(self) -> str:
        props = self._get_props()
        return self._get_render_iframe(props, return_iframe=False)

    def to_code(self, dataset_name: str = "df", variable_name: str = "walker", include_import: bool = True) -> str:
        """Export a reproducible Python snippet for the current spec state."""
        if not variable_name.isidentifier() or keyword.iskeyword(variable_name):
            raise ValueError("variable_name must be a valid Python identifier")

        from pygwalker import __version__

        spec_obj = self.spec_manager.build_spec_obj(self.spec_version or __version__)
        spec_json = json.dumps(spec_obj, ensure_ascii=False, separators=(",", ":"))
        lines = []
        if include_import:
            lines.extend(["import pygwalker as pyg", ""])
        lines.append(f"spec = {spec_json!r}")
        lines.append(f"{variable_name} = pyg.walk({dataset_name}, spec=spec)")
        return "\n".join(lines)

    def display_on_convert_html(self):
        """
        Display on jupyter-nbconvert html.
        """
        self._get_jupyter_display_manager().display_on_convert_html()

    def display_on_jupyter(self):
        """
        Display on jupyter notebook/lab.
        If share has large data loading, only sample data can be displayed when reload.
        After that, it will be changed to python for data calculation,
        and only a small amount of data will be output to the front end to complete the analysis of big data.
        """
        _warn_legacy_jupyter_transport("PygWalker.display_on_jupyter()")
        self._get_jupyter_display_manager().display_on_jupyter()

    def display_on_jupyter_use_widgets(self, iframe_width: Optional[str] = None, iframe_height: Optional[str] = None):
        """
        use the legacy ipywidgets text bridge, Display on jupyter notebook/lab.
        When the kernel is down, the chart will not be displayed, so use `display_on_jupyter` to share
        """
        _warn_legacy_jupyter_transport("PygWalker.display_on_jupyter_use_widgets()")
        self._get_jupyter_display_manager().display_on_jupyter_use_widgets(iframe_width, iframe_height)

    def display_on_jupyter_use_anywidget(self):
        """
        Display on Jupyter notebook/lab using the cross-notebook anywidget transport.
        """
        self._get_jupyter_display_manager().display_on_jupyter_use_anywidget()

    def display_preview_on_jupyter(self):
        """
        Display preview on jupyter notebook/lab.
        """
        self._get_jupyter_display_manager().display_preview_on_jupyter()

    @property
    def chart_list(self) -> List[str]:
        """
        Get the list of saved charts.
        """
        return self.spec_manager.chart_list

    def save_chart_to_file(self, chart_name: str, path: str, save_type: Literal["html", "png", "svg"] = "png"):
        """
        Save the chart to a file.
        """
        self._get_chart_export_manager().save_chart_to_file(chart_name, path, save_type)

    def export_chart_html(self, chart_name: str) -> str:
        """
        Export the chart as a html string.
        """
        return self._get_chart_export_manager().export_chart_html(chart_name)

    def export_chart_png(self, chart_name: str) -> bytes:
        """
        Export the chart as a png bytes.
        """
        return self._get_chart_export_manager().export_chart_png(chart_name)

    def export_chart_svg(self, chart_name: str) -> bytes:
        """Export the chart as svg bytes."""
        return self._get_chart_export_manager().export_chart_svg(chart_name)

    def display_chart(self, chart_name: str, *, title: Optional[str] = None, desc: str = ""):
        """
        Display the chart in the notebook.
        """
        self._get_chart_export_manager().display_chart(chart_name, title=title, desc=desc)

    def get_single_chart_html_by_spec(
        self,
        *,
        spec: Dict[str, Any],
        title: str = "",
        desc: str = "",
    ) -> str:
        return self._get_chart_export_manager().get_single_chart_html_by_spec(spec=spec, title=title, desc=desc)

    def _get_chart_by_name(self, chart_name: str) -> ChartData:
        return self.spec_manager.get_chart_by_name(chart_name)

    def _get_jupyter_display_manager(self) -> JupyterDisplayManager:
        display_manager = getattr(self, "jupyter_display_manager", None)
        if display_manager is None:
            display_manager = JupyterDisplayManager(self, lambda content: display_html(content))
        return display_manager

    def _get_chart_export_manager(self) -> ChartExportManager:
        export_manager = getattr(self, "chart_export_manager", None)
        if export_manager is None:
            export_manager = ChartExportManager(self, lambda content: display_html(content))
        return export_manager

    def _get_props_tracker(self) -> PropsTracker:
        props_tracker = getattr(self, "props_tracker", None)
        if props_tracker is None:
            props_tracker = PropsTracker(self, lambda event, props: track_event(event, props))
        return props_tracker

    def _init_callback(self, comm: BaseCommunication, preview_tool: PreviewImageTool = None):
        CommHandler(
            self,
            comm,
            preview_tool=preview_tool,
            upload_tool_cls=BatchUploadDatasToolOnWidgets,
        ).register()

    def _get_props(
        self, env: str = "", data_source: Optional[Dict[str, Any]] = None, need_load_datas: bool = False
    ) -> Dict[str, Any]:
        props_builder = getattr(self, "props_builder", None)
        if props_builder is None:
            props_builder = PropsBuilder(self, lambda: get_local_user_id())
        props = props_builder.build(env, data_source, need_load_datas)
        self._get_props_tracker().track_invocation(props)

        return props

    def _get_render_iframe(
        self,
        props: Dict[str, Any],
        return_iframe: bool = True,
        iframe_width: Optional[str] = None,
        iframe_height: Optional[str] = None,
    ) -> str:
        """Get render iframe html."""
        return self.render_manager.get_render_iframe(props, return_iframe, iframe_width, iframe_height)

    def _get_gw_preview_html(self, manual: bool = False) -> str:
        """
        'manual' represents the user actively calling to obtain preview_html. It will randomly generate a gid, keeping it separate from the logic of walker automatically generating the preview part.
        """
        return self.render_manager.get_preview_html(manual)

    def _get_gw_chart_preview_html(self, chart_name: int, title: str, desc: str) -> str:
        return self.render_manager.get_chart_preview_html(chart_name, title, desc)
