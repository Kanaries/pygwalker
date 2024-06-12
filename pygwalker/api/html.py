from typing import Union, Dict, Optional, Any, List
import logging

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.services.data_parsers import get_parser
from pygwalker.services.preview_image import render_gw_chart_preview_html
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from pygwalker.utils.randoms import generate_hash_code
from pygwalker.utils.check_walker_params import check_expired_params

logger = logging.getLogger(__name__)


def _to_html(
    df: DataFrame,
    gid: Union[int, str] = None,
    *,
    spec: str = "",
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    default_tab: Literal["data", "vis"] = "vis",
    gw_mode: Literal['explore', 'renderer', 'filter_renderer', 'table'] = "explore",
    width: Optional[int] = None,
    height: Optional[int] = None,
    **kwargs
) -> str:
    """
    Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - spec (str): chart config data. config id, json, remote file url
        - theme_key ('vega' | 'g2' | 'streamlit'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    check_expired_params(kwargs)

    if gid is None:
        gid = generate_hash_code()

    if field_specs is None:
        field_specs = []

    walker = PygWalker(
        gid=gid,
        dataset=df,
        field_specs=field_specs,
        spec=spec,
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
        **kwargs
    )

    return walker.to_html(width, height)


def to_html(
    df: DataFrame,
    gid: Union[int, str] = None,
    *,
    spec: str = "",
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs
) -> str:
    """
    Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - spec (str): chart config data. config id, json, remote file url
        - theme_key ('vega' | 'g2'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
    """
    return _to_html(
        df,
        gid,
        spec=spec,
        field_specs=field_specs,
        theme_key=theme_key,
        appearance=appearance,
        default_tab=default_tab,
        **kwargs
    )


def to_table_html(
    df: DataFrame,
    *,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    **kwargs
) -> str:
    """
    Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    return _to_html(
        df,
        None,
        spec="",
        field_specs=[],
        theme_key=theme_key,
        appearance=appearance,
        gw_mode="table",
        height="800px",
        **kwargs
    )


def to_render_html(
    df: DataFrame,
    spec: str,
    *,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    **kwargs
) -> str:
    """
    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - spec (str): chart config data. config id, json, remote file url

    Kargs:
        - theme_key ('vega' | 'g2'): theme type.
        - appearance ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    return _to_html(
        df,
        None,
        spec=spec,
        field_specs=[],
        theme_key=theme_key,
        appearance=appearance,
        gw_mode="filter_renderer",
        **kwargs
    )


def to_chart_html(
    dataset: Union[DataFrame, Connector, str],
    spec: Dict[str, Any],
    *,
    spec_type: Literal["graphic-walker", "vega"] = "graphic-walker",
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
) -> str:
    """
    Generate HTML code of a chart by graphic-walker or vega spec.

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataset.
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
        single_vis_spec=gw_dsl,
        data=data,
        theme_key=theme_key,
        appearance=appearance,
        title="",
        desc=""
    )
