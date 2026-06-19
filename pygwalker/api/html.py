from typing import Union, Dict, Optional, Any, List
import logging

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.services.data_parsers import get_parser
from pygwalker.services.preview_image import render_gw_chart_preview_html
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IComputation, IThemeKey
from pygwalker.utils.randoms import generate_hash_code
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils.spec import resolve_spec_input
from pygwalker.api._walker_reuse import (
    collect_walker_construction_conflicts,
    is_public_walker,
    reject_walker_construction_params,
)

logger = logging.getLogger(__name__)


def _to_html_from_walker(
    walker,
    gid: Union[int, str] = None,
    *,
    spec: str = "",
    spec_path: Optional[str] = None,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    default_tab: Literal["data", "vis"] = "vis",
    computation: Optional[IComputation] = None,
    **kwargs,
) -> str:
    width = kwargs.pop("width", None)
    height = kwargs.pop("height", None)
    conflicts = collect_walker_construction_conflicts(
        {
            "gid": gid,
            "spec": spec,
            "spec_path": spec_path,
            "field_specs": field_specs,
            "theme_key": theme_key,
            "appearance": appearance,
            "default_tab": default_tab,
            "computation": computation,
        },
        {
            "gid": None,
            "spec": "",
            "spec_path": None,
            "field_specs": None,
            "theme_key": "g2",
            "appearance": "media",
            "default_tab": "vis",
            "computation": None,
        },
        extra_kwargs=kwargs,
        present_extra_conflicts=("kernel_computation", "cloud_computation", "use_kernel_calc"),
    )
    reject_walker_construction_params("pygwalker.to_html()", conflicts)
    return walker.to_html(width, height)


def _pop_static_html_computation_kwargs(kwargs: Dict[str, Any], computation: Optional[IComputation]) -> None:
    if computation is not None and computation not in ("auto", "browser", "kernel", "cloud"):
        raise ValueError("`computation` must be one of 'auto', 'browser', 'kernel', or 'cloud'.")

    computation_flags = ("kernel_computation", "cloud_computation", "use_kernel_calc")
    enabled_flags = [name for name in computation_flags if kwargs.get(name) is True]
    if computation in ("kernel", "cloud"):
        enabled_flags.append(f"computation='{computation}'")
    if enabled_flags:
        flags = ", ".join(enabled_flags)
        raise ValueError(
            f"Static HTML export does not support kernel or cloud computation ({flags}). "
            "Use pygwalker.walk/render in a live backend for kernel/cloud computation, "
            "or omit these options for browser-only static HTML."
        )
    for name in computation_flags:
        kwargs.pop(name, None)


def _to_html(
    df: DataFrame,
    gid: Union[int, str] = None,
    *,
    spec: str = "",
    spec_path: Optional[str] = None,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    default_tab: Literal["data", "vis"] = "vis",
    computation: Optional[IComputation] = None,
    gw_mode: Literal["explore", "renderer", "filter_renderer", "table"] = "explore",
    width: Optional[int] = None,
    height: Optional[int] = None,
    **kwargs,
) -> str:
    """
    Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pandas.DataFrame | polars.DataFrame | pyarrow.Table, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - spec (str): chart config data. config id, json, remote file url
        - theme_key ('vega' | 'g2' | 'streamlit'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    check_expired_params(kwargs)
    _pop_static_html_computation_kwargs(kwargs, computation)

    resolved_spec = resolve_spec_input(spec, spec_path)

    if gid is None:
        gid = generate_hash_code()

    if field_specs is None:
        field_specs = []

    walker = PygWalker(
        gid=gid,
        dataset=df,
        field_specs=field_specs,
        spec=resolved_spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=False,
        use_save_tool=False,
        gw_mode=gw_mode,
        is_export_dataframe=False,
        kanaries_api_key="",
        default_tab=default_tab,
        cloud_computation=False,
        **kwargs,
    )

    return walker.to_html(width, height)


def to_html(
    df: DataFrame,
    gid: Union[int, str] = None,
    *,
    spec: str = "",
    spec_path: Optional[str] = None,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    default_tab: Literal["data", "vis"] = "vis",
    computation: Optional[IComputation] = None,
    **kwargs,
) -> str:
    """
    Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pandas.DataFrame | polars.DataFrame | pyarrow.Table | pygwalker.Walker, optional): dataframe or reusable Walker object.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - spec (str): chart config data. config id, json, remote file url
        - spec_path (str): local chart configuration file path. Prefer this over passing a file path through `spec`.
        - theme_key ('vega' | 'g2'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
        - computation (Literal["auto", "browser"]): static HTML always uses browser computation.
    """
    if is_public_walker(df):
        return _to_html_from_walker(
            df,
            gid,
            spec=spec,
            spec_path=spec_path,
            field_specs=field_specs,
            theme_key=theme_key,
            appearance=appearance,
            default_tab=default_tab,
            computation=computation,
            **kwargs,
        )

    return _to_html(
        df,
        gid,
        spec=spec,
        spec_path=spec_path,
        field_specs=field_specs,
        theme_key=theme_key,
        appearance=appearance,
        default_tab=default_tab,
        computation=computation,
        **kwargs,
    )


def to_table_html(
    df: DataFrame,
    *,
    spec_path: Optional[str] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    computation: Optional[IComputation] = None,
    **kwargs,
) -> str:
    """
    Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pandas.DataFrame | polars.DataFrame | pyarrow.Table, optional): dataframe.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    return _to_html(
        df,
        None,
        spec="",
        spec_path=spec_path,
        field_specs=[],
        theme_key=theme_key,
        appearance=appearance,
        computation=computation,
        gw_mode="table",
        height="800px",
        **kwargs,
    )


def to_render_html(
    df: DataFrame,
    spec: str = "",
    *,
    spec_path: Optional[str] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    computation: Optional[IComputation] = None,
    **kwargs,
) -> str:
    """
    Args:
        - df (pandas.DataFrame | polars.DataFrame | pyarrow.Table, optional): dataframe.
        - spec (str): chart config data. config id, json, remote file url

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    return _to_html(
        df,
        None,
        spec=spec,
        spec_path=spec_path,
        field_specs=[],
        theme_key=theme_key,
        appearance=appearance,
        computation=computation,
        gw_mode="filter_renderer",
        **kwargs,
    )


def to_chart_html(
    dataset: Union[DataFrame, Connector, str],
    spec: Dict[str, Any],
    *,
    spec_type: Literal["graphic-walker", "vega"] = "graphic-walker",
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
) -> str:
    """
    Generate HTML code of a chart by graphic-walker or vega spec.

    Args:
        - dataset (pandas.DataFrame | polars.DataFrame | pyarrow.Table | Connector | str, optional): dataset.
        - spec (Dict[str, Any]): chart config data.

    Kargs:
        - spec_type (Literal["graphic-walker", "vega"]): type of spec.
        - theme_key ('vega' | 'g2'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    # pylint: disable=import-outside-toplevel
    # Since the compatibility of quick js is not certain, the related methods are lazy loaded.
    from pygwalker.utils.dsl_transform import vega_to_dsl, dsl_to_workflow

    data_parser = get_parser(dataset)
    if spec_type == "vega":
        gw_dsl = vega_to_dsl(spec, data_parser.raw_fields)
    else:
        gw_dsl = spec
    workflow = dsl_to_workflow(gw_dsl)

    data = data_parser.get_datas_by_payload(workflow)
    return render_gw_chart_preview_html(
        single_vis_spec=gw_dsl, data=data, theme_key=theme_key, appearance=appearance, title="", desc=""
    )
