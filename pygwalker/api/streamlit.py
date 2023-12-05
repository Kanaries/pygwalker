from typing import Union, Dict, Optional, TYPE_CHECKING, List, Any
from distutils.version import StrictVersion
import json

from typing_extensions import Literal
from pydantic import BaseModel
import arrow
import streamlit.components.v1 as components

from .pygwalker import PygWalker
from pygwalker.communications.streamlit_comm import hack_streamlit_server, BASE_URL_PATH
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame
from pygwalker.utils.randoms import rand_str
from pygwalker.services.streamlit_components import render_explore_modal_button

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator


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
        fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
        themeKey: Literal['vega', 'g2'] = 'g2',
        dark: Literal['media', 'light', 'dark'] = 'media',
        spec: str = "",
        debug: bool = False,
        use_kernel_calc: bool = True,
        **kwargs
    ):
        """Get pygwalker html render to streamlit

        Args:
            - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
            - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

        Kargs:
            - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker. Default as 'Jupyter'
            - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
            - themeKey ('vega' | 'g2'): theme type.
            - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
            - spec (str): chart config data. config id, json, remote file url
            - debug (bool): Whether to use debug mode, Default to False.
            - use_kernel_calc(bool): Whether to use kernel compute for datas, Default to True.
        """
        self.walker = PygWalker(
            gid=gid,
            dataset=dataset,
            field_specs=fieldSpecs if fieldSpecs is not None else {},
            spec=spec,
            source_invoke_code="",
            hidedata_source_config=True,
            theme_key=themeKey,
            dark=dark,
            show_cloud_tool=False,
            use_preview=False,
            store_chart_data=False,
            use_kernel_calc=isinstance(dataset, Connector) or use_kernel_calc,
            use_save_tool=debug,
            is_export_dataframe=False,
            **kwargs
        )
        self.walker.init_streamlit_comm()
        self.global_pre_filters = None

    def _get_html(
        self,
        *,
        mode: Literal["explore", "renderer"] = "explore",
        vis_spec: Optional[List[Dict[str, Any]]] = None,
        **params: Dict[str, Any]
    ) -> str:
        """
        Get the html for streamlit.
        Params will update origin props.
        """
        props = self.walker._get_props("streamlit")

        props["communicationUrl"] = BASE_URL_PATH
        props["gwMode"] = mode
        if vis_spec is not None:
            props["visSpec"] = vis_spec

        props.update(params)

        html = self.walker._get_render_iframe(props, False)
        return html

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

    def render_explore(
        self,
        width: int = 1300,
        height: int = 1000,
        scrolling: bool = False,
    ) -> "DeltaGenerator":
        """Render explore UI(it can drag and drop fields)"""
        html = self._get_html()
        return components.html(html, height=height, width=width, scrolling=scrolling)

    def render_pure_chart(
        self,
        index: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
        scrolling: bool = False,
        pre_filters: Optional[List[PreFilter]] = None,
    ) -> "DeltaGenerator":
        """
        Render pure chart, index is the order of chart, starting from 0.
        If you set `pre_filters`, it will overwritre global_pre_filters.
        """
        cur_spec_obj = self.walker.vis_spec[index]

        if StrictVersion(self.walker.spec_version) > StrictVersion("0.3.11"):
            chart_size_config = cur_spec_obj["layout"]["size"]
        else:
            chart_size_config = cur_spec_obj["config"]["size"]

        chart_size_config["mode"] = "fixed"
        explore_button_size = 20
        if pre_filters is None:
            pre_filters = self.global_pre_filters

        if pre_filters is not None:
            pre_filters_json = self._convert_pre_filters_to_gw_config(
                pre_filters, cur_spec_obj
            )
            cur_spec_obj["encodings"]["filters"].extend(pre_filters_json)

        if width is None:
            width = chart_size_config["width"]
            left = width + 6
        else:
            width = width - explore_button_size - 6
            chart_size_config["width"] = width
            left = width + 6

        if height is None:
            height = chart_size_config["height"]
        else:
            chart_size_config["height"] = height

        html = self._get_html(
            mode="renderer",
            vis_spec=[cur_spec_obj]
        )

        explore_html = self._get_html(
            vis_spec=[cur_spec_obj],
            needLoadLastSpec=False,
            useSaveTool=False
        )
        render_explore_modal_button(explore_html, left, explore_button_size)

        return components.html(html, height=height, width=width, scrolling=scrolling)


def get_streamlit_html(
    dataset: Union[DataFrame, Connector],
    gid: Union[int, str] = None,
    *,
    fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
    themeKey: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    spec: str = "",
    use_kernel_calc: bool = False,
    debug: bool = False,
    **kwargs
) -> str:
    """Get pygwalker html render to streamlit

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - themeKey ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - use_kernel_calc(bool): Whether to use kernel compute for datas, Default to False.
        - debug (bool): Whether to use debug mode, Default to False.
    """
    if fieldSpecs is None:
        fieldSpecs = {}

    renderer = StreamlitRenderer(
        gid=gid,
        dataset=dataset,
        fieldSpecs=fieldSpecs,
        spec=spec,
        themeKey=themeKey,
        dark=dark,
        debug=debug,
        use_kernel_calc=use_kernel_calc,
        **kwargs
    )

    return renderer._get_html()
