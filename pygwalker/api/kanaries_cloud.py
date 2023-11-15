from typing import Dict, Optional

from .pygwalker import PygWalker
from pygwalker.data_parsers.base import FieldSpec
from pygwalker._typing import DataFrame
from pygwalker.utils.display import display_html
from pygwalker.services.cloud_service import create_cloud_graphic_walker, get_cloud_graphic_walker


def create_cloud_walker(
    dataset: DataFrame,
    *,
    chart_name: str,
    workspace_name: str,
    fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
) -> str:
    """Create a pygwalker in kanaries cloud

    Args:
        - dataset (pl.DataFrame | pd.DataFrame, optional): dataframe.

    Kargs:
        - chart_name (str): pygwalker chart name in kanaries cloud.
        - workspace_name (str): kanaries workspace name.
        - fieldSpecs (Dict[str, FieldSpec]): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.

    Returns:
        str: pygwalker url in kanaries cloud
    """
    if fieldSpecs is None:
        fieldSpecs = {}

    walker = PygWalker(
        gid=None,
        dataset=dataset,
        field_specs=fieldSpecs,
        spec="",
        source_invoke_code="",
        hidedata_source_config=True,
        theme_key="vega",
        dark="media",
        show_cloud_tool=False,
        use_preview=False,
        store_chart_data=False,
        use_kernel_calc=False,
        use_save_tool=False,
        gw_mode="explore",
        is_export_dataframe=False,
    )

    create_cloud_graphic_walker(
        chart_name=chart_name,
        workspace_name=workspace_name,
        dataset_content=walker.data_parser.to_csv(),
        field_specs=walker.field_specs
    )


def walk_on_cloud(workspace_name: str, chart_name: str):
    """render a pygwalker in kanaries cloud

    Args:
        - chart_name (str): pygwalker chart name in kanaries cloud.
        - workspace_name (str): kanaries workspace name.
    """

    cloud_url = get_cloud_graphic_walker(workspace_name, chart_name)

    iframe_html = f"""
        <iframe
            width="100%"
            height="900px"
            src="{cloud_url}"
            frameborder="0"
            allow="clipboard-read; clipboard-write"
            allowfullscreen>
        </iframe>
    """

    display_html(iframe_html)
