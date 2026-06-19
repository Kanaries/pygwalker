from typing import Union, List, Optional, TYPE_CHECKING

from typing_extensions import Literal

from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IComputation, IThemeKey
from pygwalker.utils.runtime_env import get_current_env
from pygwalker.api import jupyter
from pygwalker.api import webserver

if TYPE_CHECKING:
    from pygwalker.api.walker import Walker


def walk(
    dataset: Union[DataFrame, Connector, str, "Walker"],
    gid: Union[int, str] = None,
    *,
    env: Literal["Jupyter", "JupyterWidget"] = "JupyterWidget",
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec: str = "",
    spec_path: Optional[str] = None,
    computation: Optional[IComputation] = None,
    use_kernel_calc: Optional[bool] = None,
    kernel_computation: Optional[bool] = None,
    cloud_computation: bool = False,
    show_cloud_tool: bool = True,
    kanaries_api_key: str = "",
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs,
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
        - spec_path (str): local chart configuration file path. Prefer this over passing a file path through `spec`.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "auto".
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None, automatically determine whether to use kernel calculation.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
        - cloud_computation(bool): Whether to use cloud compute for datas, it upload your data to kanaries cloud. Default to False.
        - port(int): only works in web server mode. port to use for the server. Default to None, which means a random port will be used.
    """
    cur_env = get_current_env()
    if cur_env == "jupyter":
        return jupyter.walk(
            dataset,
            gid,
            env=env,
            field_specs=field_specs,
            theme_key=theme_key,
            appearance=appearance,
            spec=spec,
            spec_path=spec_path,
            computation=computation,
            use_kernel_calc=use_kernel_calc,
            kernel_computation=kernel_computation,
            cloud_computation=cloud_computation,
            show_cloud_tool=show_cloud_tool,
            kanaries_api_key=kanaries_api_key,
            default_tab=default_tab,
            **kwargs,
        )

    return webserver.walk(
        dataset,
        gid,
        field_specs=field_specs,
        theme_key=theme_key,
        appearance=appearance,
        spec=spec,
        spec_path=spec_path,
        computation=computation,
        kernel_computation=kernel_computation,
        cloud_computation=cloud_computation,
        show_cloud_tool=show_cloud_tool,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        auto_open=True,
        auto_shutdown=True,
        **kwargs,
    )


def render(
    dataset: Union[DataFrame, Connector, str],
    spec: str = "",
    *,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec_path: Optional[str] = None,
    computation: Optional[IComputation] = None,
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    **kwargs,
):
    """
    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - spec (str): chart config data. config id, json, remote file url
        - spec_path (str): local chart configuration file path. Prefer this over passing a file path through `spec`.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "auto".
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - port(int): only works in web server mode. port to use for the server. Default to None, which means a random port will be used.
    """
    cur_env = get_current_env()
    if cur_env == "jupyter":
        return jupyter.render(
            dataset,
            spec,
            theme_key=theme_key,
            appearance=appearance,
            spec_path=spec_path,
            computation=computation,
            kernel_computation=kernel_computation,
            kanaries_api_key=kanaries_api_key,
            **kwargs,
        )

    return webserver.render(
        dataset,
        spec,
        theme_key=theme_key,
        appearance=appearance,
        spec_path=spec_path,
        computation=computation,
        kernel_computation=kernel_computation,
        kanaries_api_key=kanaries_api_key,
        auto_open=True,
        auto_shutdown=True,
        **kwargs,
    )


def table(
    dataset: Union[DataFrame, Connector, str],
    *,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec_path: Optional[str] = None,
    computation: Optional[IComputation] = None,
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    **kwargs,
):
    """
    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec_path (str): local chart configuration file path.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "auto".
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
        - port(int): only works in web server mode. port to use for the server. Default to None, which means a random port will be used.
    """
    cur_env = get_current_env()
    if cur_env == "jupyter":
        return jupyter.table(
            dataset,
            theme_key=theme_key,
            appearance=appearance,
            spec_path=spec_path,
            computation=computation,
            kernel_computation=kernel_computation,
            kanaries_api_key=kanaries_api_key,
            **kwargs,
        )

    return webserver.table(
        dataset,
        theme_key=theme_key,
        appearance=appearance,
        spec_path=spec_path,
        computation=computation,
        kernel_computation=kernel_computation,
        kanaries_api_key=kanaries_api_key,
        auto_open=True,
        auto_shutdown=True,
        **kwargs,
    )
