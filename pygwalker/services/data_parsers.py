import sys
from typing import Dict, Optional, Union, Any, List

from pygwalker.data_parsers.base import BaseDataParser, FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame

__classname2method = {}


# pylint: disable=import-outside-toplevel
def _get_data_parser(dataset: Union[DataFrame, Connector, str]) -> BaseDataParser:
    """
    Get DataFrameDataParser for dataset
    TODO: Maybe you can find a better way to handle the following code
    """
    if type(dataset) in __classname2method:
        return __classname2method[type(dataset)]

    if 'pandas' in sys.modules:
        import pandas as pd
        if isinstance(dataset, pd.DataFrame):
            from pygwalker.data_parsers.pandas_parser import PandasDataFrameDataParser
            __classname2method[pd.DataFrame] = PandasDataFrameDataParser
            return __classname2method[pd.DataFrame]

    if 'polars' in sys.modules:
        import polars as pl
        if isinstance(dataset, pl.DataFrame):
            from pygwalker.data_parsers.polars_parser import PolarsDataFrameDataParser
            __classname2method[pl.DataFrame] = PolarsDataFrameDataParser
            return __classname2method[pl.DataFrame]

    if 'modin.pandas' in sys.modules:
        from modin import pandas as mpd
        if isinstance(dataset, mpd.DataFrame):
            from pygwalker.data_parsers.modin_parser import ModinPandasDataFrameDataParser
            __classname2method[mpd.DataFrame] = ModinPandasDataFrameDataParser
            return __classname2method[mpd.DataFrame]

    if 'pyspark' in sys.modules:
        from pyspark.sql import DataFrame as SparkDataFrame
        if isinstance(dataset, SparkDataFrame):
            from pygwalker.data_parsers.spark_parser import SparkDataFrameDataParser
            __classname2method[SparkDataFrame] = SparkDataFrameDataParser
            return __classname2method[SparkDataFrame]

    if isinstance(dataset, Connector):
        from pygwalker.data_parsers.database_parser import DatabaseDataParser
        __classname2method[DatabaseDataParser] = DatabaseDataParser
        return __classname2method[DatabaseDataParser]

    if isinstance(dataset, str):
        from pygwalker.data_parsers.cloud_dataset_parser import CloudDatasetParser
        __classname2method[CloudDatasetParser] = CloudDatasetParser
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

    parser = _get_data_parser(dataset)(
        dataset,
        field_specs,
        infer_string_to_date,
        infer_number_to_dimension,
        other_params
    )
    return parser
