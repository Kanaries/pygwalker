import sys
import hashlib
import pandas as pd
from typing import Dict, Optional, Union, Any, List, Tuple
from typing_extensions import Literal

from pygwalker.data_parsers.base import BaseDataParser, FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame

__classname2method = {}

DatasetType = Literal['pandas', 'polars', 'modin', 'pyspark', 'connector', 'cloud_dataset']


# pylint: disable=import-outside-toplevel
def _get_data_parser(dataset: Union[DataFrame, Connector, str]) -> Tuple[BaseDataParser, DatasetType]:
    """
    Get DataFrameDataParser for dataset
    TODO: Maybe you can find a better way to handle the following code
    """
    if type(dataset) in __classname2method:
        return __classname2method[type(dataset)]

    if isinstance(dataset, pd.DataFrame):
        from pygwalker.data_parsers.pandas_parser import PandasDataFrameDataParser
        __classname2method[pd.DataFrame] = (PandasDataFrameDataParser, "pandas")
        return __classname2method[pd.DataFrame]

    if 'polars' in sys.modules:
        import polars as pl
        if isinstance(dataset, pl.DataFrame):
            from pygwalker.data_parsers.polars_parser import PolarsDataFrameDataParser
            __classname2method[pl.DataFrame] = (PolarsDataFrameDataParser, "polars")
            return __classname2method[pl.DataFrame]

    if 'modin.pandas' in sys.modules:
        from modin import pandas as mpd
        if isinstance(dataset, mpd.DataFrame):
            from pygwalker.data_parsers.modin_parser import ModinPandasDataFrameDataParser
            __classname2method[mpd.DataFrame] = (ModinPandasDataFrameDataParser, "modin")
            return __classname2method[mpd.DataFrame]

    if 'pyspark' in sys.modules:
        from pyspark.sql import DataFrame as SparkDataFrame
        if isinstance(dataset, SparkDataFrame):
            from pygwalker.data_parsers.spark_parser import SparkDataFrameDataParser
            __classname2method[SparkDataFrame] = (SparkDataFrameDataParser, "pyspark")
            return __classname2method[SparkDataFrame]

    if isinstance(dataset, Connector):
        from pygwalker.data_parsers.database_parser import DatabaseDataParser
        __classname2method[DatabaseDataParser] = (DatabaseDataParser, "connector")
        return __classname2method[DatabaseDataParser]

    if isinstance(dataset, str):
        from pygwalker.data_parsers.cloud_dataset_parser import CloudDatasetParser
        __classname2method[CloudDatasetParser] = (CloudDatasetParser, "cloud_dataset")
        return __classname2method[CloudDatasetParser]

    raise TypeError(f"Unsupported data type: {type(dataset)}")


def get_parser(
    dataset: Union[DataFrame, Connector, str],
    field_specs: Optional[List[FieldSpec]] = None,
    infer_string_to_date: bool = False,
    infer_number_to_dimension: bool = True,
    other_params: Optional[Dict[str, Any]] = None
) -> BaseDataParser:
    if field_specs is None:
        field_specs = []
    if other_params is None:
        other_params = {}

    parser_func, _ = _get_data_parser(dataset)
    parser = parser_func(
        dataset,
        field_specs,
        infer_string_to_date,
        infer_number_to_dimension,
        other_params
    )
    return parser


def _get_pl_dataset_hash(dataset: DataFrame) -> str:
    """Get polars dataset hash value."""
    import polars as pl
    row_count = dataset.shape[0]
    other_info = str(dataset.shape) + "_polars"
    if row_count > 4000:
        dataset = pl.concat([dataset[:2000], dataset[-2000:]])
    hash_bytes = dataset.hash_rows().to_numpy().tobytes() + other_info.encode()
    return hashlib.md5(hash_bytes).hexdigest()


def _get_pd_dataset_hash(dataset: DataFrame) -> str:
    """Get pandas dataset hash value."""
    row_count = dataset.shape[0]
    other_info = str(dataset.shape) + "_pandas"
    if row_count > 4000:
        dataset = pd.concat([dataset[:2000], dataset[-2000:]])
    hash_bytes = pd.util.hash_pandas_object(dataset).values.tobytes() + other_info.encode()
    return hashlib.md5(hash_bytes).hexdigest()


def _get_modin_dataset_hash(dataset: DataFrame) -> str:
    """Get modin dataset hash value."""
    import modin.pandas as mpd
    row_count = dataset.shape[0]
    other_info = str(dataset.shape) + "_modin"
    if row_count > 4000:
        dataset = mpd.concat([dataset[:2000], dataset[-2000:]])
    dataset = dataset._to_pandas()
    hash_bytes = pd.util.hash_pandas_object(dataset).values.tobytes() + other_info.encode()
    return hashlib.md5(hash_bytes).hexdigest()


def _get_spark_dataset_hash(dataset: DataFrame) -> str:
    """Get pyspark dataset hash value."""
    shape = ((dataset.count(), len(dataset.columns)))
    row_count = shape[0]
    other_info = str(shape) + "_pyspark"
    if row_count > 4000:
        dataset = dataset.limit(4000)
    dataset_pd = dataset.toPandas()
    hash_bytes = pd.util.hash_pandas_object(dataset_pd).values.tobytes() + other_info.encode()
    return hashlib.md5(hash_bytes).hexdigest()


def get_dataset_hash(dataset: Union[DataFrame, Connector, str]) -> str:
    """Just a less accurate way to get different dataset hash values."""
    _, dataset_type = _get_data_parser(dataset)

    if dataset_type == "polars":
        return _get_pl_dataset_hash(dataset)

    if dataset_type == "pandas":
        return _get_pd_dataset_hash(dataset)

    if dataset_type == "modin":
        return _get_modin_dataset_hash(dataset)

    if dataset_type == "pyspark":
        return _get_spark_dataset_hash(dataset)

    if dataset_type == "connector":
        return hashlib.md5("_".join([dataset.url, dataset.view_sql, dataset_type]).encode()).hexdigest()

    if dataset_type == "cloud_dataset":
        return hashlib.md5("_".join([dataset, dataset_type]).encode()).hexdigest()
