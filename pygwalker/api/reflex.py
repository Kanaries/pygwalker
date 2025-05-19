from typing import Union, List, Optional

import reflex as rx
from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.communications.reflex_comm import (
    BASE_URL_PATH,
    ReflexCommunication,
)
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, ISpecIOMode, IThemeKey
from pygwalker.utils.check_walker_params import check_expired_params


# pylint: disable=protected-access

def get_component(
    dataset: Union[DataFrame, Connector],
    gid: Union[int, str] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec: str = "",
    spec_io_mode: ISpecIOMode = "r",
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs,
) -> rx.Component:
    """Get a Reflex component that renders Pygwalker."""
    check_expired_params(kwargs)

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs if field_specs is not None else [],
        spec=spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=isinstance(dataset, Connector) or kernel_computation,
        use_save_tool="w" in spec_io_mode,
        is_export_dataframe=False,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=False,
        gw_mode="explore",
        **kwargs,
    )

    props = walker._get_props("reflex")
    props["communicationUrl"] = BASE_URL_PATH
    comm = ReflexCommunication(str(walker.gid))
    walker._init_callback(comm)

    html = walker._get_render_iframe(props, True)
    return rx.html(html)
