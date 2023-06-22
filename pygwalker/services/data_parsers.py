import sys

from pygwalker.data_parsers.base import DataFramePropParser
from pygwalker._typing import DataFrame

__classname2method = {}


# pylint: disable=import-outside-toplevel
def _get_prop_getter(df: DataFrame) -> DataFramePropParser:
    """
    Get DataFramePropParser for df
    TODO: Maybe you can find a better way to handle the following code

    """
    if type(df) in __classname2method:
        return __classname2method[type(df)]

    if 'pandas' in sys.modules:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            from pygwalker.data_parsers.pandas_parser import PandasDataFramePropParser
            __classname2method[pd.DataFrame] = PandasDataFramePropParser
            return __classname2method[pd.DataFrame]

    if 'polars' in sys.modules:
        import polars as pl
        if isinstance(df, pl.DataFrame):
            from pygwalker.data_parsers.polars_parser import PolarsDataFramePropParser
            __classname2method[pl.DataFrame] = PolarsDataFramePropParser
            return __classname2method[pl.DataFrame]

    if 'modin.pandas' in sys.modules:
        from modin import pandas as mpd
        if isinstance(df, mpd.DataFrame):
            from pygwalker.data_parsers.modin_parser import ModinPandasDataFramePropParser
            __classname2method[mpd.DataFrame] = ModinPandasDataFramePropParser
            return __classname2method[mpd.DataFrame]

    return DataFramePropParser


def get_parser(df: DataFrame) -> DataFramePropParser:
    parser = _get_prop_getter(df)
    return parser
