from typing import Union, Dict, Optional, Any
import inspect

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec, BaseDataParser
from pygwalker._typing import DataFrame
from pygwalker.services.data_parsers import get_parser
from pygwalker.services.format_invoke_walk_code import get_formated_spec_params_code_from_frame
from pygwalker.utils.execute_env_check import check_convert


def walk(
    df: Union[DataFrame, Any],
    gid: Union[int, str] = None,
    *,
    custom_data_parser: Optional[BaseDataParser] = None,
    env: Literal['Jupyter', 'Streamlit', 'JupyterWidget'] = 'JupyterWidget',
    fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
    hideDataSourceConfig: bool = True,
    themeKey: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    return_html: bool = False,
    spec: str = "",
    show_cloud_tool: bool = False,
    use_preview: bool = False,
    store_chart_data: bool = False,
    **kwargs
):
    """Walk through pandas.DataFrame df with Graphic Walker

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker. Default as 'Jupyter'
        - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - return_html (bool, optional): Directly return a html string. Defaults to False.
        - spec (str): chart config data. config id, json, remote file url
        - show_cloud_tool(bool): Whether to use kanaries cloud function, Default to False.
        - use_preview(bool): Whether to use preview function, Default to False.
        - store_chart_data(bool): Whether to save chart to disk, only work when spec is json file, Default to False.
    """
    if fieldSpecs is None:
        fieldSpecs = {}

    source_invoke_code = get_formated_spec_params_code_from_frame(
        inspect.stack()[1].frame
    )

    if custom_data_parser is None:
        data_parser = get_parser(df)
    else:
        data_parser = custom_data_parser(df)

    walker = PygWalker(
        gid,
        data_parser.to_records(),
        data_parser.raw_fields(field_specs=fieldSpecs),
        spec,
        source_invoke_code,
        hideDataSourceConfig,
        themeKey,
        dark,
        show_cloud_tool,
        use_preview,
        store_chart_data,
        **kwargs
    )

    if return_html:
        return walker.to_html()

    if check_convert():
        env = "JupyterConvert"

    env_display_map = {
        "Streamlit": walker.display_on_streamlit,
        "JupyterWidget": walker.display_on_jupyter_use_widgets,
        "Jupyter": walker.display_on_jupyter,
        "JupyterConvert": walker.display_on_convert_html,
    }

    display_func = env_display_map.get(env, lambda: None)
    display_func()

    return walker
