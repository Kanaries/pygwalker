from typing import Union, Dict, Optional
import inspect

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame
from pygwalker.services.format_invoke_walk_code import get_formated_spec_params_code_from_frame
from pygwalker.services.kaggle import auto_set_kanaries_api_key_on_kaggle, adjust_kaggle_default_font_size
from pygwalker.utils.execute_env_check import check_convert, get_kaggle_run_type, check_kaggle
from pygwalker.utils.check_walker_params import check_expired_params


def walk(
    dataset: Union[DataFrame, Connector, str],
    gid: Union[int, str] = None,
    *,
    env: Literal['Jupyter', 'JupyterWidget'] = 'JupyterWidget',
    field_specs: Optional[Dict[str, FieldSpec]] = None,
    hide_data_source_config: bool = True,
    theme_key: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    return_html: bool = False,
    spec: str = "",
    use_preview: bool = True,
    store_chart_data: bool = False,
    use_kernel_calc: bool = False,
    show_cloud_tool: bool = True,
    kanaries_api_key: str = "",
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs
):
    """Walk through pandas.DataFrame df with Graphic Walker

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - env: (Literal['Jupyter' | 'JupyterWidget'], optional): The enviroment using pygwalker. Default as 'JupyterWidget'
        - field_specs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - hide_data_source_config (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - theme_key ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - return_html (bool, optional): Directly return a html string. Defaults to False.
        - spec (str): chart config data. config id, json, remote file url
        - use_preview(bool): Whether to use preview function, Default to False.
        - store_chart_data(bool): Whether to save chart to disk, only work when spec is json file, Default to False.
        - use_kernel_calc(bool): Whether to use kernel compute for datas, Default to False.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
    """
    check_expired_params(kwargs)

    if field_specs is None:
        field_specs = {}

    source_invoke_code = get_formated_spec_params_code_from_frame(
        inspect.stack()[1].frame
    )

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=spec,
        source_invoke_code=source_invoke_code,
        hidedata_source_config=hide_data_source_config,
        theme_key=theme_key,
        dark=dark,
        show_cloud_tool=show_cloud_tool,
        use_preview=use_preview,
        store_chart_data=store_chart_data,
        use_kernel_calc=isinstance(dataset, (Connector, str)) or use_kernel_calc,
        use_save_tool=True,
        gw_mode="explore",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        **kwargs
    )

    if return_html:
        return walker.to_html()

    if check_kaggle():
        auto_set_kanaries_api_key_on_kaggle()

    if get_kaggle_run_type() == "batch":
        adjust_kaggle_default_font_size()
        env = "JupyterPreview"
    elif check_convert():
        env = "JupyterConvert"

    env_display_map = {
        "JupyterWidget": walker.display_on_jupyter_use_widgets,
        "Jupyter": walker.display_on_jupyter,
        "JupyterConvert": walker.display_on_convert_html,
        "JupyterPreview": walker.display_preview_on_jupyter
    }

    display_func = env_display_map.get(env, lambda: None)
    display_func()

    return walker
