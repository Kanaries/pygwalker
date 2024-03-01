from typing import Union, Dict, Optional
import logging
import traceback

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker._typing import DataFrame
from pygwalker.utils.randoms import generate_hash_code
from pygwalker.utils.check_walker_params import check_expired_params

logger = logging.getLogger(__name__)


def to_html(
    df: DataFrame,
    gid: Union[int, str] = None,
    *,
    spec: str = "",
    field_specs: Optional[Dict[str, FieldSpec]] = None,
    theme_key: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs
):
    """
    Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - field_specs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - spec (str): chart config data. config id, json, remote file url
        - theme_key ('vega' | 'g2'): theme type.
        - dark ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    check_expired_params(kwargs)

    if gid is None:
        gid = generate_hash_code()

    if field_specs is None:
        field_specs = {}

    walker = PygWalker(
        gid=gid,
        dataset=df,
        field_specs=field_specs,
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        dark=dark,
        show_cloud_tool=False,
        use_preview=False,
        use_kernel_calc=False,
        use_save_tool=False,
        gw_mode="explore",
        is_export_dataframe=False,
        kanaries_api_key="",
        default_tab=default_tab,
        **kwargs
    )

    try:
        html = walker.to_html()
    except Exception as e:
        logger.error(traceback.format_exc())
        return f"<div>{str(e)}</div>"
    return html
