from typing import Union, List, Optional, TYPE_CHECKING
import inspect
import warnings

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IComputation, IThemeKey
from pygwalker.services.format_invoke_walk_code import get_formated_spec_params_code_from_frame
from pygwalker.services.kaggle import auto_set_kanaries_api_key_on_kaggle, adjust_kaggle_default_font_size
from pygwalker.utils.execute_env_check import check_convert, get_kaggle_run_type, check_kaggle
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils.computation import resolve_computation_mode
from pygwalker.utils.spec import resolve_spec_input
from pygwalker.api._walker_reuse import (
    collect_walker_construction_conflicts,
    get_callable_defaults,
    is_public_walker,
    reject_walker_construction_params,
)

if TYPE_CHECKING:
    from pygwalker.api.walker import Walker


_LEGACY_JUPYTER_ENVS = {
    "Jupyter": "JupyterAnywidget",
    "JupyterWidget": "JupyterAnywidget",
}
_DELEGATED_WALKER_SHOW_WARNING_PATTERN = r"`Walker\.show\(env=.*legacy Jupyter transport"
_CORE_LEGACY_TRANSPORT_WARNING_PATTERN = r"`PygWalker\.display_on_jupyter.*legacy Jupyter transport"


def _warn_legacy_jupyter_env(env: str) -> None:
    replacement = _LEGACY_JUPYTER_ENVS.get(env)
    if replacement is None:
        return

    warnings.warn(
        f"`env='{env}'` uses a legacy Jupyter transport and is deprecated. "
        f"Use `env='{replacement}'` or omit `env` to use the anywidget transport.",
        DeprecationWarning,
        stacklevel=3,
    )


def _show_public_walker(dataset: "Walker", env: str) -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=_DELEGATED_WALKER_SHOW_WARNING_PATTERN,
            category=DeprecationWarning,
        )
        dataset.show(env)


def _call_display_func(env: str, display_func) -> None:
    if env not in _LEGACY_JUPYTER_ENVS:
        display_func()
        return

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=_CORE_LEGACY_TRANSPORT_WARNING_PATTERN,
            category=DeprecationWarning,
        )
        display_func()


def _reject_walker_construction_params(
    *,
    gid: Union[int, str],
    field_specs: Optional[List[FieldSpec]],
    theme_key: IThemeKey,
    appearance: IAppearance,
    spec: str,
    spec_path: Optional[str],
    computation: Optional[IComputation],
    use_kernel_calc: Optional[bool],
    kernel_computation: Optional[bool],
    cloud_computation: bool,
    show_cloud_tool: bool,
    kanaries_api_key: str,
    default_tab: Literal["data", "vis"],
    kwargs,
) -> None:
    values = {
        "gid": gid,
        "field_specs": field_specs,
        "theme_key": theme_key,
        "appearance": appearance,
        "spec": spec,
        "spec_path": spec_path,
        "computation": computation,
        "use_kernel_calc": use_kernel_calc,
        "kernel_computation": kernel_computation,
        "cloud_computation": cloud_computation,
        "show_cloud_tool": show_cloud_tool,
        "kanaries_api_key": kanaries_api_key,
        "default_tab": default_tab,
    }
    conflicts = collect_walker_construction_conflicts(
        values,
        get_callable_defaults(walk, values),
        conflict_predicates={
            "cloud_computation": lambda value: value not in (False, None),
            "show_cloud_tool": lambda value: value is not True,
        },
        extra_kwargs=kwargs,
    )
    reject_walker_construction_params("jupyter.walk()", conflicts)


def walk(
    dataset: Union[DataFrame, Connector, str, "Walker"],
    gid: Union[int, str] = None,
    *,
    env: Literal["JupyterAnywidget", "Jupyter", "JupyterWidget"] = "JupyterAnywidget",
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
    """Walk through a tabular dataset with Graphic Walker

    Args:
        - dataset (pandas.DataFrame | polars.DataFrame | pyarrow.Table | Connector | str | pygwalker.Walker, optional): dataset or reusable Walker object.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - env: (Literal['JupyterAnywidget' | 'Jupyter' | 'JupyterWidget'], optional): The environment using pygwalker. Default as 'JupyterAnywidget'. 'Jupyter' and 'JupyterWidget' are deprecated legacy transports kept for compatibility.
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
    """
    check_expired_params(kwargs)

    if check_kaggle():
        auto_set_kanaries_api_key_on_kaggle()

    if get_kaggle_run_type() == "batch":
        adjust_kaggle_default_font_size()
        env = "JupyterPreview"
    elif check_convert():
        env = "JupyterConvert"

    _warn_legacy_jupyter_env(env)

    if is_public_walker(dataset):
        _reject_walker_construction_params(
            gid=gid,
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
            kwargs=kwargs,
        )
        _show_public_walker(dataset, env)
        return dataset.core

    if field_specs is None:
        field_specs = []

    source_invoke_code = get_formated_spec_params_code_from_frame(inspect.stack()[1].frame)

    resolved_spec = resolve_spec_input(spec, spec_path)
    resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
        dataset,
        computation=computation,
        kernel_computation=kernel_computation,
        cloud_computation=cloud_computation,
        use_kernel_calc=use_kernel_calc,
    )
    if env == "JupyterConvert":
        enabled_live_computation_params = []
        if computation in ("kernel", "cloud"):
            enabled_live_computation_params.append(f"computation='{computation}'")
        if kernel_computation is True:
            enabled_live_computation_params.append("kernel_computation=True")
        if use_kernel_calc is True:
            enabled_live_computation_params.append("use_kernel_calc=True")
        if cloud_computation is True:
            enabled_live_computation_params.append("cloud_computation=True")
        if enabled_live_computation_params:
            params = ", ".join(enabled_live_computation_params)
            raise ValueError(
                f"JupyterConvert/static HTML output does not support kernel or cloud computation ({params}). "
                "Use computation='browser' or run pygwalker in a live backend."
            )
        resolved_kernel_computation = False
        resolved_cloud_computation = False

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=resolved_spec,
        source_invoke_code=source_invoke_code,
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=show_cloud_tool,
        use_preview=True,
        kernel_computation=resolved_kernel_computation,
        use_save_tool=True,
        gw_mode="explore",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=resolved_cloud_computation,
        **kwargs,
    )

    env_display_map = {
        "JupyterAnywidget": walker.display_on_jupyter_use_anywidget,
        "JupyterWidget": walker.display_on_jupyter_use_widgets,
        "Jupyter": walker.display_on_jupyter,
        "JupyterConvert": walker.display_on_convert_html,
        "JupyterPreview": walker.display_preview_on_jupyter,
    }

    display_func = env_display_map.get(env, lambda: None)
    _call_display_func(env, display_func)

    return walker


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
        - dataset (pandas.DataFrame | polars.DataFrame | pyarrow.Table | Connector | str, optional): dataset.
        - spec (str): chart config data. config id, json, remote file url
        - spec_path (str): local chart configuration file path. Prefer this over passing a file path through `spec`.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "auto".
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
    """
    resolved_spec = resolve_spec_input(spec, spec_path)
    resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
        dataset,
        computation=computation,
        kernel_computation=kernel_computation,
    )

    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=[],
        spec=resolved_spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=resolved_kernel_computation,
        use_save_tool=False,
        gw_mode="filter_renderer",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab="vis",
        cloud_computation=resolved_cloud_computation,
        **kwargs,
    )

    walker.display_on_jupyter_use_widgets()


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
        - dataset (pandas.DataFrame | polars.DataFrame | pyarrow.Table | Connector | str, optional): dataset.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec_path (str): local chart configuration file path.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "auto".
        - kernel_computation(bool): Whether to use kernel compute for datas, Default to None.
        - kanaries_api_key (str): kanaries api key, Default to "".
    """
    resolved_spec = resolve_spec_input("", spec_path)
    resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
        dataset,
        computation=computation,
        kernel_computation=kernel_computation,
    )
    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=[],
        spec=resolved_spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=resolved_kernel_computation,
        use_save_tool=False,
        gw_mode="table",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab="vis",
        cloud_computation=resolved_cloud_computation,
        **kwargs,
    )

    walker.display_on_jupyter_use_widgets(iframe_height="800px")
