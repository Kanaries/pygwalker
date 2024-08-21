from typing import Union, List, Optional
import inspect

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from pygwalker.services.format_invoke_walk_code import get_formated_spec_params_code_from_frame
from pygwalker.services.kaggle import auto_set_kanaries_api_key_on_kaggle, adjust_kaggle_default_font_size
from pygwalker.utils.execute_env_check import check_convert, get_kaggle_run_type, check_kaggle
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils import fallback_value


def walk(
    dataset: Union[DataFrame, Connector, str],
    gid: Union[int, str] = None,
    *,
    env: Literal['Jupyter', 'JupyterWidget'] = 'JupyterWidget',
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    spec: str = "",
    use_kernel_calc: Optional[bool] = None,
    kernel_computation: Optional[bool] = None,
    cloud_computation: bool = False,
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
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - theme_key ('vega' | 'g2' | 'streamlit'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - use_kernel_calc(bool): Whether to use kernel compute for datas, Default to None, automatically determine whether to use kernel calculation.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
        - cloud_computation(bool): Whether to use cloud compute for datas, it upload your data to kanaries cloud. Default to False.
    """
    check_expired_params(kwargs)

    if field_specs is None:
        field_specs = []

    source_invoke_code = get_formated_spec_params_code_from_frame(
        inspect.stack()[1].frame
    )

    if check_kaggle():
        auto_set_kanaries_api_key_on_kaggle()

    if get_kaggle_run_type() == "batch":
        adjust_kaggle_default_font_size()
        env = "JupyterPreview"
    elif check_convert():
        env = "JupyterConvert"

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=spec,
        source_invoke_code=source_invoke_code,
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=show_cloud_tool,
        use_preview=True,
        kernel_computation=env != "JupyterConvert" and (isinstance(dataset, (Connector, str)) or fallback_value(kernel_computation, use_kernel_calc)),
        use_save_tool=True,
        gw_mode="explore",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=cloud_computation,
        **kwargs
    )

    env_display_map = {
        "JupyterWidget": walker.display_on_jupyter_use_widgets,
        "Jupyter": walker.display_on_jupyter,
        "JupyterConvert": walker.display_on_convert_html,
        "JupyterPreview": walker.display_preview_on_jupyter
    }

    display_func = env_display_map.get(env, lambda: None)
    display_func()

    return walker


def render(
    dataset: Union[DataFrame, Connector, str],
    spec: str,
    *,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    **kwargs
):
    """
    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - spec (str): chart config data. config id, json, remote file url

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
    """

    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=[],
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=isinstance(dataset, (Connector, str)) or kernel_computation,
        use_save_tool=False,
        gw_mode="filter_renderer",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab="vis",
        cloud_computation=False,
        **kwargs
    )

    walker.display_on_jupyter_use_widgets()


def table(
    dataset: Union[DataFrame, Connector, str],
    *,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    **kwargs
):
    """
    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
    """
    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=[],
        spec="",
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=isinstance(dataset, (Connector, str)) or kernel_computation,
        use_save_tool=False,
        gw_mode="table",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab="vis",
        cloud_computation=False,
        **kwargs
    )

    walker.display_on_jupyter_use_widgets(iframe_height="800px")
