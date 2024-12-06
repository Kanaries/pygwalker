from typing import Union, List, Optional, Dict, Any
from pygwalker.communications.base import BaseCommunication

from typing_extensions import Literal
import json
from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from bottle import Bottle, request, response, run
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils import fallback_value
from pygwalker.utils.encode import DataFrameEncoder

def start_server(walker: PygWalker):
    comm = BaseCommunication(walker.gid)
    walker._init_callback(comm)
    app = Bottle()
    # api path and html path need to have the same prefix
    @app.post("/comm/")
    @app.post("/comm/<gid>")
    def pygwalker_comm(gid):       
        payload = request.json
        comm_obj = walker.comm
        result = comm_obj._receive_msg(payload["action"], payload["data"])
        response.content_type = 'application/json'
        return json.dumps(result, cls=DataFrameEncoder)


    # api path and html path need to have the same prefix
    @app.get("/")
    def pyg_html():
        props = walker._get_props("web_server")
        props["communicationUrl"] = "comm"
        html = walker._get_render_iframe(props, True)
        return html
    
    port = 3000
    while True:
        try:
            run(app, host='0.0.0.0', port=port)
            break
        except OSError as e:
            if e.errno == 48:  # Address already in use
                port += 1
            else:
                raise


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

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=show_cloud_tool,
        use_preview=False,
        kernel_computation=(isinstance(dataset, (Connector, str)) or fallback_value(kernel_computation, use_kernel_calc)),
        is_export_dataframe=False,
        use_save_tool=False,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=cloud_computation,
        gw_mode="explore",
    )
    start_server(walker)
    
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

    start_server(walker)

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

    start_server(walker)