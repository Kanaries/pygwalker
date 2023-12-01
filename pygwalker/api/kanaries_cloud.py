from typing import Dict, Optional, Union
from datetime import datetime
import hashlib

from pygwalker.data_parsers.base import FieldSpec
from pygwalker._typing import DataFrame
from pygwalker.utils.display import display_html
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.services.cloud_service import create_cloud_graphic_walker, get_cloud_graphic_walker
from pygwalker.services.data_parsers import get_parser
from pygwalker.services.cloud_service import create_file_dataset, create_datasource, create_database_dataset, get_datasource_by_name


def _get_database_type_from_dialect_name(dialect_name: str) -> str:
    type_map = {
        "postgresql": "postgres",
    }
    type_name = type_map.get(dialect_name, dialect_name)
    return type_name[0].upper() + type_name[1:]


def create_cloud_dataset(
    dataset: Union[DataFrame, Connector],
    *,
    name: Optional[str] = None,
    is_public: bool = False,
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
    data_parser = get_parser(dataset, False, None)
    if name is None:
        name = f"pygwalker_{datetime.now().strftime('%Y%m%d%H%M')}"

    if data_parser.dataset_tpye == "cloud_dataset":
        raise ValueError("dataset is already a cloud dataset")

    if data_parser.dataset_tpye.startswith("connector"):
        datasource_name = "pygwalker_" + hashlib.md5(dataset.url.encode()).hexdigest()
        datasource_id = get_datasource_by_name(datasource_name)
        if datasource_id is None:
            datasource_id = create_datasource(
                datasource_name,
                dataset.url,
                _get_database_type_from_dialect_name(dataset.dialect_name)
            )
        dataset_id = create_database_dataset(
            name,
            datasource_id,
            is_public,
            dataset.view_sql
        )
        return dataset_id
    else:
        dataset_id = create_file_dataset(
            name,
            data_parser.to_parquet(),
            [field["name"] for field in data_parser.raw_fields],
            is_public
        )

    return dataset_id


def create_cloud_walker(
    dataset: DataFrame,
    *,
    chart_name: str,
    workspace_name: str,
    fieldSpecs: Optional[Dict[str, FieldSpec]] = None,
) -> str:
    """
    (deprecated)
    Create a pygwalker in kanaries cloud

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

    data_parser = get_parser(dataset, False, fieldSpecs)

    create_cloud_graphic_walker(
        chart_name=chart_name,
        workspace_name=workspace_name,
        dataset_content=data_parser.to_parquet(),
        field_specs=data_parser.raw_fields
    )


def walk_on_cloud(workspace_name: str, chart_name: str):
    """
    (deprecated)
    render a pygwalker in kanaries cloud

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
