from typing import Union, List, Optional, Any, Dict, TYPE_CHECKING
import inspect
import json

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IComputation, IThemeKey
from pygwalker.services.format_invoke_walk_code import get_formated_spec_params_code_from_frame
from pygwalker.communications.anywidget_comm import AnywidgetCommunication
from pygwalker.utils.computation import resolve_computation_mode
from pygwalker.utils.frontend_assets import read_frontend_asset
from pygwalker.utils.spec import resolve_spec_input
import anywidget
import traitlets

if TYPE_CHECKING:
    from pygwalker.api.walker import Walker


class _WalkerWidget(anywidget.AnyWidget):
    """WalkerWidget"""

    _esm = read_frontend_asset("pygwalker-app.es.js", encoding="utf-8")
    props = traitlets.Unicode("").tag(sync=True)


def _is_public_walker(value: Any) -> bool:
    from pygwalker.api.walker import Walker

    return isinstance(value, Walker)


def _reject_walker_construction_params(
    *,
    gid: Union[int, str],
    field_specs: Optional[List[FieldSpec]],
    theme_key: IThemeKey,
    appearance: IAppearance,
    spec: str,
    spec_path: Optional[str],
    computation: Optional[IComputation],
    show_cloud_tool: bool,
    kanaries_api_key: str,
    default_tab: Literal["data", "vis"],
    kwargs: Dict[str, Any],
) -> None:
    conflicting_options = []
    if gid is not None:
        conflicting_options.append("gid")
    if field_specs is not None:
        conflicting_options.append("field_specs")
    if theme_key != "g2":
        conflicting_options.append("theme_key")
    if appearance != "media":
        conflicting_options.append("appearance")
    if spec not in ("", None):
        conflicting_options.append("spec")
    if spec_path is not None:
        conflicting_options.append("spec_path")
    if computation is not None:
        conflicting_options.append("computation")
    if show_cloud_tool is not False:
        conflicting_options.append("show_cloud_tool")
    if kanaries_api_key:
        conflicting_options.append("kanaries_api_key")
    if default_tab != "vis":
        conflicting_options.append("default_tab")
    if kwargs:
        conflicting_options.extend(sorted(kwargs))
    if conflicting_options:
        params = ", ".join(conflicting_options)
        raise ValueError(
            f"anywidget.walk() received a Walker object and cannot apply construction parameters: {params}. "
            "Pass those options when creating pygwalker.Walker instead."
        )


def walk(
    dataset: Union[DataFrame, Connector, str, "Walker"],
    gid: Union[int, str] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec: str = "",
    spec_path: Optional[str] = None,
    computation: Optional[IComputation] = None,
    show_cloud_tool: bool = False,
    kanaries_api_key: str = "",
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs,
):
    """Walk through pandas.DataFrame df with Graphic Walker

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - theme_key ('vega' | 'g2' | 'streamlit'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - spec_path (str): local chart configuration file path. Prefer this over passing a file path through `spec`.
        - computation (Literal["auto", "browser", "kernel", "cloud"]): computation backend. Default to "kernel".
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
    """
    if _is_public_walker(dataset):
        _reject_walker_construction_params(
            gid=gid,
            field_specs=field_specs,
            theme_key=theme_key,
            appearance=appearance,
            spec=spec,
            spec_path=spec_path,
            computation=computation,
            show_cloud_tool=show_cloud_tool,
            kanaries_api_key=kanaries_api_key,
            default_tab=default_tab,
            kwargs=kwargs,
        )
        widget = _WalkerWidget()
        walker = dataset.core
        walker.use_preview = False
        comm = AnywidgetCommunication(walker.gid)
        widget.props = json.dumps(walker._get_props("anywidget", []))
        comm.register_widget(widget)
        walker._init_callback(comm)
        return widget

    if field_specs is None:
        field_specs = []

    source_invoke_code = get_formated_spec_params_code_from_frame(inspect.stack()[1].frame)

    widget = _WalkerWidget()
    resolved_spec = resolve_spec_input(spec, spec_path)
    resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
        dataset,
        computation=computation,
        default_kernel_computation=True,
    )
    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=resolved_spec,
        source_invoke_code=source_invoke_code,
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=show_cloud_tool,
        use_preview=False,
        kernel_computation=resolved_kernel_computation,
        use_save_tool=True,
        gw_mode="explore",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=resolved_cloud_computation,
        **kwargs,
    )
    comm = AnywidgetCommunication(walker.gid)

    widget.props = json.dumps(walker._get_props("anywidget", []))
    comm.register_widget(widget)
    walker._init_callback(comm)

    return widget
