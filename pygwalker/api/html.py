from typing import Union, Dict, Optional
import logging
import traceback

from typing_extensions import Literal

from pygwalker.props_parsers.base import DataFrame, FieldSpec
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.props_parsers import get_props
from pygwalker.services.render import render_gwalker_html


def to_html(
    df: DataFrame,
    gid: Union[int, str] = None,
    *,
    fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
    hideDataSourceConfig: bool = True,
    themeKey: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    **kwargs
):
    """Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.

        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark ('media' | 'light' | 'dark'): 'media': auto detect OS theme.
    """
    if gid is None:
        gid = GlobalVarManager.get_global_gid()

    if fieldSpecs is None:
        fieldSpecs = {}

    try:
        props = get_props(
            df,
            hideDataSourceConfig=hideDataSourceConfig,
            themeKey=themeKey,
            dark=dark,
            fieldSpecs=fieldSpecs,
            **kwargs
        )
        html = render_gwalker_html(gid, props)
    except Exception as e:
        logging.error(traceback.format_exc())
        return f"<div>{str(e)}</div>"
    return html
