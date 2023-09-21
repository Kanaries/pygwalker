from typing import Union, Dict, Optional

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
        - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker. Default as 'Jupyter'
        - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - debug (bool): Whether to use debug mode, Default to False.
    """
    if fieldSpecs is None:
        fieldSpecs = {}

    walker = PygWalker(
        gid,
        dataset,
        fieldSpecs,
        spec,
        "",
        hideDataSourceConfig,
        themeKey,
        dark,
        False,
        False,
        False,
        isinstance(dataset, Connector) or use_kernel_calc,
        debug,
        **kwargs
    )

    return walker.get_html_on_streamlit_v2()
