from typing import Union, List, Optional
from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.communications.gradio_comm import (
    BASE_URL_PATH,
    GradioCommunication,
    PYGWALKER_ROUTE
)
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame
from pygwalker.utils.check_walker_params import check_expired_params


# pylint: disable=protected-access
def get_html_on_gradio(
    dataset: Union[DataFrame, Connector],
    gid: Union[int, str] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    spec: str = "",
    spec_io_mode: Literal["r", "rw"] = "r",
    use_kernel_calc: bool = True,
    kanaries_api_key: str = "",
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs
) -> str:
    """Get pygwalker html render to gradio

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker. Default as 'Jupyter'
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - theme_key ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - spec_io_mode (Literal["r", "rw"]): spec io mode, Default to "r", "r" for read, "rw" for read and write.
        - use_kernel_calc(bool): Whether to use kernel compute for datas, Default to True.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
    """
    check_expired_params(kwargs)

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs if field_specs is not None else [],
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        dark=dark,
        show_cloud_tool=False,
        use_preview=False,
        use_kernel_calc=isinstance(dataset, Connector) or use_kernel_calc,
        use_save_tool="w" in spec_io_mode,
        is_export_dataframe=False,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        use_cloud_calc=False,
        gw_mode="explore",
        **kwargs
    )

    props = walker._get_props("gradio")
    props["communicationUrl"] = BASE_URL_PATH
    comm = GradioCommunication(str(walker.gid))
    walker._init_callback(comm)

    html = walker._get_render_iframe(props, True)
    return html
