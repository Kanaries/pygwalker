from typing import Union, Dict, Optional
import logging
import traceback

from typing_extensions import Literal

from pygwalker.data_parsers.base import FieldSpec
from pygwalker._typing import DataFrame
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.data_parsers import get_parser
from pygwalker.services.props import get_default_props
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

    data_parser = get_parser(df)
    df = data_parser.escape_fname(df)

    try:
        props = get_default_props(
            data_parser.to_records(df),
            data_parser.raw_fields(df, fieldSpecs=fieldSpecs),
            hideDataSourceConfig=hideDataSourceConfig,
            themeKey=themeKey,
            dark=dark,
            **kwargs
        )
        html = render_gwalker_html(gid, props)
    except Exception as e:
        logging.error(traceback.format_exc())
        return f"<div>{str(e)}</div>"
    return html
