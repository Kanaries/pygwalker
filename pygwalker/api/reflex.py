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
from pygwalker._typing import DataFrame, IAppearance, IComputation, ISpecIOMode, IThemeKey
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils.computation import resolve_computation_mode
from pygwalker.utils.spec import resolve_spec_input


# pylint: disable=protected-access


def get_component(
    dataset: Union[DataFrame, Connector],
    gid: Union[int, str] = None,
    *,
    field_specs: Optional[List[FieldSpec]] = None,
    theme_key: IThemeKey = "g2",
    appearance: IAppearance = "media",
    spec: str = "",
    spec_path: Optional[str] = None,
    spec_io_mode: ISpecIOMode = "r",
    computation: Optional[IComputation] = None,
    kernel_computation: Optional[bool] = None,
    kanaries_api_key: str = "",
    default_tab: Literal["data", "vis"] = "vis",
    **kwargs,
) -> rx.Component:
    """Get a Reflex component that renders Pygwalker."""
    check_expired_params(kwargs)

    resolved_spec = resolve_spec_input(spec, spec_path)
    resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
        dataset,
        computation=computation,
        kernel_computation=kernel_computation,
    )
    if resolved_kernel_computation or resolved_cloud_computation:
        raise ValueError("Reflex integration does not support kernel or cloud computation. Use computation='browser'.")

    walker = PygWalker(
        gid=gid,
        dataset=dataset,
        field_specs=field_specs if field_specs is not None else [],
        spec=resolved_spec,
        source_invoke_code="",
        theme_key=theme_key,
        appearance=appearance,
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=resolved_kernel_computation,
        use_save_tool="w" in spec_io_mode,
        is_export_dataframe=False,
        kanaries_api_key=kanaries_api_key,
        default_tab=default_tab,
        cloud_computation=resolved_cloud_computation,
        gw_mode="explore",
        **kwargs,
    )

    props = walker._get_props("reflex")
    props["communicationUrl"] = BASE_URL_PATH
    comm = ReflexCommunication(str(walker.gid))
    walker._init_callback(comm)

    html = walker._get_render_iframe(props, True)
    return rx.html(html)
