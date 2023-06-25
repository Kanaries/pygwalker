import sys

from pygwalker.data_parsers.base import BaseDataParser
from pygwalker._typing import DataFrame

__classname2method = {}


# pylint: disable=import-outside-toplevel
def _get_data_parser(df: DataFrame) -> BaseDataParser:
    """
    Get DataFrameDataParser for df
    TODO: Maybe you can find a better way to handle the following code
    """
    if type(df) in __classname2method:
        return __classname2method[type(df)]

    if 'pandas' in sys.modules:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            from pygwalker.data_parsers.pandas_parser import PandasDataFrameDataParser
            __classname2method[pd.DataFrame] = PandasDataFrameDataParser
            return __classname2method[pd.DataFrame]

    if 'polars' in sys.modules:
        import polars as pl
        if isinstance(df, pl.DataFrame):
            from pygwalker.data_parsers.polars_parser import PolarsDataFrameDataParser
            __classname2method[pl.DataFrame] = PolarsDataFrameDataParser
            return __classname2method[pl.DataFrame]

    if 'modin.pandas' in sys.modules:
        from modin import pandas as mpd
        if isinstance(df, mpd.DataFrame):
            from pygwalker.data_parsers.modin_parser import ModinPandasDataFrameDataParser
            __classname2method[mpd.DataFrame] = ModinPandasDataFrameDataParser
            return __classname2method[mpd.DataFrame]

    raise TypeError(f"Unsupported data type: {type(df)}")


def get_parser(df: DataFrame) -> BaseDataParser:
    parser = _get_data_parser(df)(df)
    return parser
