from typing import Union, Dict, Optional, List, Any, Tuple
from packaging.version import Version
from copy import deepcopy
import json

from typing_extensions import Literal, deprecated
from pydantic import BaseModel
from cachetools import cached, TTLCache
import arrow

from .pygwalker import PygWalker
from pygwalker.communications.streamlit_comm import (
    hack_streamlit_server,
    BASE_URL_PATH,
    StreamlitCommunication
)
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, ISpecIOMode, IThemeKey
from pygwalker.utils.randoms import rand_str
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils import fallback_value
from pygwalker.services.streamlit_components import pygwalker_component
from pygwalker.services.data_parsers import get_dataset_hash


class PreFilter(BaseModel):
    """
    Pre Filter.
    example:
        1. use temporal range: pass in millisecond timestamp.
        PreFilter(field="date", op="temporal range", value=[1293840000000, 1297641600000])
        PreFilter(field="date", op="temporal range", value=["2019-01-01", "2020-01-01"])
        2. use range: pass in number.
        PreFilter(field="age", op="range", value=[0, 100])
        3. use one of: pass in string or number.
        PreFilter(field="category", op="one of", value=["a", "b", "c"])
    """
    field: str
    op: Literal["range", "temporal range", "one of"]
    value: List[Union[int, float, str]]


def init_streamlit_comm():
    """Initialize pygwalker communication in streamlit"""
    hack_streamlit_server()


# pylint: disable=protected-access
class StreamlitRenderer:
    """Streamlit Renderer"""
    def __init__(
        self,
        dataset: Union[DataFrame, Connector],
        gid: Union[int, str] = None,
        *,
        field_specs: Optional[List[FieldSpec]] = None,
        theme_key: IThemeKey = 'g2',
        appearance: IAppearance = 'media',
        spec: str = "",
        spec_io_mode: ISpecIOMode = "r",
        kernel_computation: Optional[bool] = None,
        use_kernel_calc: Optional[bool] = True,
        show_cloud_tool: Optional[bool] = None,
        kanaries_api_key: str = "",
        default_tab: Literal["data", "vis"] = "vis",
        **kwargs
    ):
        """Get pygwalker html render to streamlit.
        In Streamlit, pygwalker calculates a somewhat inaccurate gid based on the dataset to 
        distinguish between datasets and uses it as the key for the Streamlit component to
        avoid redundant rendering.

        In some use case, If user frequently use the same StreamlitRenderer to receive different dataframes,
        and the differences between these dataframes are so small that pygwalker's gid calculation logic cannot distinguish between different datasets,
        user should customize method to generate a gid to differentiate between datasets.

        Args:
            - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
            - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

        Kargs:
            - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
            - theme_key ('vega' | 'g2'): theme type.
            - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
            - spec (str): chart config data. config id, json, remote file url
            - spec_io_mode (ISpecIOMode): spec io mode, Default to "r", "r" for read, "rw" for read and write.
            - kernel_computation(bool): Whether to use kernel compute for datas, Default to True.
            - use_kernel_calc(bool): Deprecated, use kernel_computation instead.
            - kanaries_api_key (str): kanaries api key, Default to "".
            - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
        """
        check_expired_params(kwargs)

        init_streamlit_comm()

        self.walker = PygWalker(
            gid=gid if gid is not None else get_dataset_hash(dataset),
            dataset=dataset,
            field_specs=field_specs if field_specs is not None else [],
            spec=spec,
            source_invoke_code="",
            theme_key=theme_key,
            appearance=appearance,
            show_cloud_tool=show_cloud_tool,
            use_preview=False,
            kernel_computation=isinstance(dataset, Connector) or fallback_value(kernel_computation, use_kernel_calc),
            use_save_tool="w" in spec_io_mode,
            is_export_dataframe=False,
            kanaries_api_key=kanaries_api_key,
            default_tab=default_tab,
            cloud_computation=False,
            gw_mode="explore",
            **kwargs
        )
        comm = StreamlitCommunication(str(self.walker.gid))
        self.walker._init_callback(comm)
        self.global_pre_filters = None

    @cached(cache=TTLCache(maxsize=256, ttl=1800))
    def _get_html_with_params_str_cache(self, params_str: str) -> str:
        params = dict(json.loads(params_str))
        mode = params.pop("mode")
        vis_spec = params.pop("vis_spec")
        kwargs = params

        props = self.walker._get_props("streamlit")

        props["communicationUrl"] = BASE_URL_PATH
        props["gwMode"] = mode
        if vis_spec is not None:
            props["visSpec"] = vis_spec

        props.update(kwargs)

        return self.walker._get_render_iframe(props, False)

    def _get_html(
        self,
        *,
        mode: Literal["explore", "renderer", "filter_renderer"] = "explore",
        vis_spec: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Dict[str, Any]
    ) -> str:
        """
        Get the html for streamlit.
        Kwargs will update origin props.
        """
        params_str = json.dumps(sorted({
            "mode": mode,
            "vis_spec": vis_spec,
            **kwargs
        }.items()))

        return self._get_html_with_params_str_cache(params_str)

    def _convert_pre_filters_to_gw_config(
        self,
        pre_filters: List[PreFilter],
        spec_obj: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        field_map = {
            field["name"]: field
            for field in spec_obj["encodings"]["dimensions"] + spec_obj["encodings"]["measures"]
        }

        gw_filters = []
        for pre_filter in pre_filters:
            if pre_filter.op == "temporal range":
                values = [
                    int(arrow.get(value).timestamp() * 1000)
                    for value in pre_filter.value
                ]
            else:
                values = pre_filter.value

            gw_filters.append({
                **field_map[pre_filter.field],
                "dragId": "gw_" + rand_str(4),
                "rule": {
                    "type": pre_filter.op,
                    "value": values
                }
            })
        return gw_filters

    def set_global_pre_filters(self, pre_filters: List[PreFilter]):
        """It will append new filters to exists charts."""
        self.global_pre_filters = pre_filters

    def viewer(self, *, key: str = "viewer"):
        """Render filter renderer UI"""
        key = f"{self.walker.gid}-{key}"
        return self._component(key=key, mode="filter_renderer")

    @deprecated("render_filter_renderer is deprecated, use viewer instead.")
    def render_filter_renderer(self, *args, **kwargs):
        return self.viewer(*args, **kwargs)

    def explorer(
        self,
        *,
        key: str = "explorer",
        default_tab: Literal["data", "vis"] = "vis"
    ):
        """Render explore UI(it can drag and drop fields)"""
        key = f"{self.walker.gid}-{key}"
        return self._component(key=key, mode="explore", defaultTab=default_tab)

    @deprecated("render_explore is deprecated, use explorer instead.")
    def render_explore(self, *args, **kwargs):
        return self.explorer(*args, **kwargs)

    def chart(
        self,
        index: int,
        *,
        key: str = "chart",
        size: Optional[Tuple[int, int]] = None,
        pre_filters: Optional[List[PreFilter]] = None,
    ):
        """
        Render pure chart, index is the order of chart, starting from 0.
        If you set `pre_filters`, it will overwritre global_pre_filters.
        """
        cur_spec_obj = deepcopy(self.walker.vis_spec[index])
        key = f"{self.walker.gid}-{key}-{index}"

        if Version(self.walker.spec_version) > Version("0.3.11"):
            chart_size_config = cur_spec_obj["layout"]["size"]
        else:
            chart_size_config = cur_spec_obj["config"]["size"]

        if pre_filters is None:
            pre_filters = self.global_pre_filters

        if pre_filters is not None:
            pre_filters_json = self._convert_pre_filters_to_gw_config(
                pre_filters, cur_spec_obj
            )
            cur_spec_obj["encodings"]["filters"].extend(pre_filters_json)

        if size is not None:
            chart_size_config["mode"] = "fixed"
            chart_size_config["width"] = size[0]
            chart_size_config["height"] = size[1]

        return self._component(key=key, mode="renderer", vis_spec=[cur_spec_obj])

    @deprecated("render_pure_chart is deprecated, use chart instead.")
    def render_pure_chart(self, *args, **kwargs):
        return self.chart(*args, **kwargs)

    def table(
        self,
        *,
        key: str = "table",
    ):
        """Render pure table UI"""
        key = f"{self.walker.gid}-{key}"
        return self._component(key=key, mode="table")

    def _component(
        self,
        *,
        key: str,
        mode: Literal["explore", "renderer", "filter_renderer", "table"],
        vis_spec: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Dict[str, Any]
    ):
        props = self.walker._get_props("streamlit", [])
        props["gwMode"] = mode
        props["communicationUrl"] = BASE_URL_PATH
        if vis_spec is not None:
            props["visSpec"] = vis_spec
        props.update(kwargs)

        component_value = pygwalker_component(props, key)
        return component_value


def get_streamlit_html(
    dataset: Union[DataFrame, Connector],
    gid: Union[int, str] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    spec: str = "",
    use_kernel_calc: Optional[bool] = None,
    kernel_computation: Optional[bool] = None,
    show_cloud_tool: Optional[bool] = None,
    spec_io_mode: ISpecIOMode = "r",
    kanaries_api_key: str = "",
    mode: Literal["explore", "filter_renderer", "table"] = "explore",
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs
) -> str:
    """Get pygwalker html render to streamlit

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - use_kernel_calc(bool): Deprecated, use kernel_computation instead.
        - spec_io_mode (ISpecIOMode): spec io mode, Default to "r", "r" for read, "rw" for read and write.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
    """
    if field_specs is None:
        field_specs = []

    renderer = StreamlitRenderer(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=spec,
        theme_key=theme_key,
        appearance=appearance,
        spec_io_mode=spec_io_mode,
        use_kernel_calc=use_kernel_calc,
        kernel_computation=kernel_computation,
        show_cloud_tool=show_cloud_tool,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        **kwargs
    )

    return renderer._get_html(mode=mode)
