from typing import Union, Dict, Optional, Any
import inspect
import html as m_html
import time

from typing_extensions import Literal

from pygwalker.utils.display import display_html
from pygwalker.data_parsers.base import FieldSpec, BaseDataParser
from pygwalker._typing import DataFrame
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.data_parsers import get_parser
from pygwalker.services.render import (
    render_gwalker_html,
    render_gwalker_iframe,
    get_max_limited_datas,
    BatchUploadDatasTool
)
from pygwalker.services.props import get_default_props
from pygwalker.services.spec import get_spec_json
from pygwalker.services.format_invoke_walk_code import get_formated_spec_params_code


def walk(
    df: Union[DataFrame, Any],
    gid: Union[int, str] = None,
    *,
    custom_data_parser: Optional[BaseDataParser] = None,
    env: Literal['Jupyter', 'Streamlit'] = 'Jupyter',
    fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
    hideDataSourceConfig: bool = True,
    themeKey: Literal['vega', 'g2'] = 'g2',
    dark: Literal['media', 'light', 'dark'] = 'media',
    return_html: bool = False,
    **kwargs
):
    """Walk through pandas.DataFrame df with Graphic Walker

    Args:
        - df (pl.DataFrame | pd.DataFrame, optional): dataframe.
        - gid (Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')

    Kargs:
        - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker. Default as 'Jupyter'
        - fieldSpecs (Dict[str, FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
        - themeKey ('vega' | 'g2'): theme type.
        - dark (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - return_html (bool, optional): Directly return a html string. Defaults to False.
        - spec (str): chart config data. config id, json, remote file url
    """
    GlobalVarManager.set_env(env)
    if fieldSpecs is None:
        fieldSpecs = {}
    if gid is None:
        gid = GlobalVarManager.get_global_gid()

    kwargs["sourceInvokeCode"] = get_formated_spec_params_code(
        inspect.stack()[1].code_context[0]
    )
    kwargs["spec"] = get_spec_json(kwargs.get("spec", ""))
    kwargs["id"] = gid

    if custom_data_parser is None:
        data_parser = get_parser(df)
    else:
        data_parser = custom_data_parser(df)

    origin_data_source = data_parser.to_records()

    props = get_default_props(
        origin_data_source,
        data_parser.raw_fields(field_specs=fieldSpecs),
        hideDataSourceConfig=hideDataSourceConfig,
        themeKey=themeKey,
        dark=dark,
        **kwargs
    )

    if return_html:
        html = render_gwalker_html(gid, props)
        srcdoc = m_html.escape(html)
        return render_gwalker_iframe(gid, srcdoc)

    props["dataSource"] = get_max_limited_datas(origin_data_source)
    html = render_gwalker_html(gid, props)
    srcdoc = m_html.escape(html)

    if len(origin_data_source) > len(props["dataSource"]):
        upload_tool = BatchUploadDatasTool()
        upload_tool.init()
        display_html(render_gwalker_iframe(gid, srcdoc), env)
        time.sleep(1)
        upload_tool.run(
            records=origin_data_source,
            sample_data_count=len(props["dataSource"]),
            data_source_id=props["dataSourceProps"]["dataSourceId"],
            gid=gid,
            tunnel_id=props["dataSourceProps"]["tunnelId"],
        )
    else:
        display_html(render_gwalker_iframe(gid, srcdoc), env)
