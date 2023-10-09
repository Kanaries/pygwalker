from typing import Union, Dict, Optional
import json

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.communications.streamlit_comm import hack_streamlit_server
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame


def init_streamlit_comm():
    """Initialize pygwalker communication in streamlit"""
    hack_streamlit_server()


def get_streamlit_html(
    dataset: Union[DataFrame, Connector],
    gid: Union[int, str] = None,
    *,
    fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
    hideDataSourceConfig: bool = True,
    themeKey: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    spec: str = "",
    use_kernel_calc: bool = False,
    debug: bool = False,
    **kwargs
):
    """Get pygwalker html render to streamlit

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - use_kernel_calc(bool): Whether to use kernel compute for datas, Default to False.
        - debug (bool): Whether to use debug mode, Default to False.
    """
    if fieldSpecs is None:
        fieldSpecs = {}

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=fieldSpecs,
        spec=spec,
        source_invoke_code="",
        hidedata_source_config=hideDataSourceConfig,
        theme_key=themeKey,
        dark=dark,
        show_cloud_tool=False,
        use_preview=False,
        store_chart_data=False,
        use_kernel_calc=isinstance(dataset, Connector) or use_kernel_calc,
        use_save_tool=debug,
        **kwargs
    )

    walker.init_streamlit_comm()

    return walker.get_html_on_streamlit_v2()


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
            **kwargs
        )
        self.walker.init_streamlit_comm()

    def render_explore(self) -> str:
        """Render explore UI(it can drag and drop fields)"""
        return self.walker.get_html_on_streamlit_v2()

    def render_pure_chart(self, index: int) -> str:
        """Render pure chart, index is the order of chart, starting from 0."""
        spec_obj = json.loads(self.walker.vis_spec)
        return self.walker.get_html_on_streamlit_v2(
            mode="renderer",
            vis_spec=json.dumps([spec_obj[index]])
        )
