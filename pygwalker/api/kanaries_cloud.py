from typing import List, Optional, Union
from datetime import datetime

from pygwalker.data_parsers.base import FieldSpec
from pygwalker._typing import DataFrame
from pygwalker.utils.display import display_html
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.services.cloud_service import CloudService
from pygwalker.services.data_parsers import get_parser


def create_cloud_dataset(
    dataset: Union[DataFrame, Connector],
    *,
    name: Optional[str] = None,
    is_public: bool = False,
    kanaries_api_key: str = ""
) -> str:
    """
    Create a dataset in kanaries cloud

    Args:
        - dataset (pl.DataFrame | pd.DataFrame | Connector, optional): dataset.

    Kargs:
        - name (str): dataset name in kanaries cloud.
        - is_public (bool): whether to make this dataset public.

    Returns:
        str: dataset id in kanaries cloud
    """
    cloud_service = CloudService(kanaries_api_key)
    data_parser = get_parser(dataset, False, None)
    if name is None:
        name = f"pygwalker_{datetime.now().strftime('%Y%m%d%H%M')}"

    dataset_id = cloud_service.create_cloud_dataset(data_parser, name, is_public)
    return dataset_id


def create_cloud_walker(
    dataset: DataFrame,
    *,
    chart_name: str,
    workspace_name: str,
    field_specs: Optional[List[FieldSpec]] = None,
    kanaries_api_key: str = ""
) -> str:
    """
    (deprecated)
    Create a pygwalker in kanaries cloud

    Args:
        - dataset (pl.DataFrame | pd.DataFrame, optional): dataframe.

    Kargs:
        - chart_name (str): pygwalker chart name in kanaries cloud.
        - workspace_name (str): kanaries workspace name.
        - field_specs (Dict[str, FieldSpec]): Specifications of some fields. They'll been automatically inferred from `df` if some fields are not specified.

    Returns:
        str: pygwalker url in kanaries cloud
    """
    if field_specs is None:
        field_specs = []

    cloud_service = CloudService(kanaries_api_key)
    data_parser = get_parser(dataset, False, field_specs)

    cloud_service.create_cloud_graphic_walker(
        chart_name=chart_name,
        workspace_name=workspace_name,
        dataset_content=data_parser.to_parquet(),
        field_specs=data_parser.raw_fields
    )


def walk_on_cloud(workspace_name: str, chart_name: str, kanaries_api_key: str = ""):
    """
    (deprecated)
    render a pygwalker in kanaries cloud

    Args:
        - chart_name (str): pygwalker chart name in kanaries cloud.
        - workspace_name (str): kanaries workspace name.
    """
    cloud_service = CloudService(kanaries_api_key)
    cloud_url = cloud_service.get_cloud_graphic_walker(workspace_name, chart_name)

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
