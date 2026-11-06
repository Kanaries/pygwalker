from typing import Any, Dict, Optional, Union

from typing_extensions import Literal

from pygwalker._typing import DataFrame, IAppearance, IThemeKey
from pygwalker.data_parsers.database_parser import Connector


def _build_display_options(
    *,
    dataset: Union[DataFrame, Connector, str],
    spec: str,
    theme_key: IThemeKey,
    appearance: IAppearance,
    kernel_computation: Optional[bool],
    cloud_computation: bool,
    kanaries_api_key: str,
    gw_mode: Literal["filter_renderer", "table"],
) -> Dict[str, Any]:
    """Assemble the shared core options for Jupyter and web render/table views.

    Callers resolve spec/computation and construct the walker themselves to keep
    warning locations and duplicate-keyword errors at the existing API boundary.
    """
    return {
        "gid": None,
        "dataset": dataset,
        "field_specs": [],
        "spec": spec,
        "source_invoke_code": "",
        "theme_key": theme_key,
        "appearance": appearance,
        "show_cloud_tool": False,
        "use_preview": False,
        "kernel_computation": kernel_computation,
        "use_save_tool": False,
        "gw_mode": gw_mode,
        "is_export_dataframe": True,
        "kanaries_api_key": kanaries_api_key,
        "default_tab": "vis",
        "cloud_computation": cloud_computation,
    }
