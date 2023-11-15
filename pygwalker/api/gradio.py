from typing import Union, Dict, Optional
from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.communications.gradio_comm import BASE_URL_PATH, PYGWALKER_ROUTE
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame


# pylint: disable=protected-access
def get_html_on_gradio(
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
) -> str:
    """Get pygwalker html render to gradio

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
    walker = PygWalker(
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

    props = walker._get_props("gradio")
    props["communicationUrl"] = BASE_URL_PATH
    walker.init_gradio_comm()

    html = walker._get_render_iframe(props, True)
    return html
