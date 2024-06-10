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
    
    parsers = [
        ('pandas', 'pandas as pd', 'pd.DataFrame', 'pygwalker.data_parsers.pandas_parser', 'PandasDataFrameDataParser'),
        ('polars', 'polars as pl', 'pl.DataFrame', 'pygwalker.data_parsers.polars_parser', 'PolarsDataFrameDataParser'),
        ('modin.pandas', 'modin.pandas as mpd', 'mpd.DataFrame', 'pygwalker.data_parsers.modin_parser', 'ModinPandasDataFrameDataParser'),
        ('pyspark.sql', 'pyspark.sql import DataFrame as SparkDataFrame', 'SparkDataFrame', 'pygwalker.data_parsers.spark_parser', 'SparkDataFrameDataParser')
    ]

    for module_name, import_stmt, dataframe_class_str, parser_module_str, parser_class_str in parsers:
        if module_name in sys.modules:
            exec(f"import {import_stmt}")  
            dataframe_class = eval(dataframe_class_str) 
            if isinstance(dataset, dataframe_class):
                exec(f"from {parser_module_str} import {parser_class_str}")
                __classname2method[dataframe_class] = eval(parser_class_str) 
                return __classname2method[dataframe_class]


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
