from typing import Union, List, Optional
import inspect
import json
import pathlib

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from pygwalker.services.format_invoke_walk_code import get_formated_spec_params_code_from_frame
from pygwalker.communications.anywidget_comm import AnywidgetCommunication
import marimo as mo
import anywidget
import traitlets


class _WalkerWidget(anywidget.AnyWidget):
    """WalkerWidget"""
    _esm = (pathlib.Path(__file__).parent.parent / "templates" / "dist" / "pygwalker-app.es.js").read_text()
    props = traitlets.Unicode("").tag(sync=True)


def walk(
    dataset: Union[DataFrame, Connector, str],
    gid: Union[int, str] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = 'g2',
    appearance: IAppearance = 'media',
    spec: str = "",
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
        - field_specs (List[FieldSpec], optional): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.
        - theme_key ('vega' | 'g2' | 'streamlit'): theme type.
        - appearance (Literal['media' | 'light' | 'dark']): 'media': auto detect OS theme.
        - spec (str): chart config data. config id, json, remote file url
        - kanaries_api_key (str): kanaries api key, Default to "".
        - default_tab (Literal["data", "vis"]): default tab to show. Default to "vis"
    """
    if field_specs is None:
        field_specs = []

    source_invoke_code = get_formated_spec_params_code_from_frame(
        inspect.stack()[1].frame
    )

    widget = _WalkerWidget()
    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs,
        spec=spec,
        source_invoke_code=source_invoke_code,
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=show_cloud_tool,
        use_preview=False,
        kernel_computation=True,
        use_save_tool=True,
        gw_mode="explore",
        is_export_dataframe=True,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=False,
        **kwargs
    )
    comm = AnywidgetCommunication(walker.gid)

    widget.props = json.dumps(walker._get_props("marimo", []))
    comm.register_widget(widget)
    walker._init_callback(comm)

    return mo.ui.anywidget(widget)
