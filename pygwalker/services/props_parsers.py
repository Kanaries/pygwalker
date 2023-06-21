import sys
from typing import Dict, Any

from pygwalker.props_parsers.base import DataFrame, DataFramePropParser

__classname2method = {}


# pylint: disable=import-outside-toplevel
def get_prop_getter(df: DataFrame) -> DataFramePropParser:
    """
    Get DataFramePropParser for df
    TODO: Maybe you can find a better way to handle the following code

    """
    if type(df) in __classname2method:
        return __classname2method[type(df)]

    if 'pandas' in sys.modules:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            from pygwalker.props_parsers.pandas_parser import PandasDataFramePropParser
            __classname2method[pd.DataFrame] = PandasDataFramePropParser
            return __classname2method[pd.DataFrame]

    if 'polars' in sys.modules:
        import polars as pl
        if isinstance(df, pl.DataFrame):
            from pygwalker.props_parsers.polars_parser import PolarsDataFramePropParser
            __classname2method[pl.DataFrame] = PolarsDataFramePropParser
            return __classname2method[pl.DataFrame]

    if 'modin.pandas' in sys.modules:
        from modin import pandas as mpd
        if isinstance(df, mpd.DataFrame):
            from pygwalker.props_parsers.modin_parser import ModinPandasDataFramePropParser
            __classname2method[mpd.DataFrame] = ModinPandasDataFramePropParser
            return __classname2method[mpd.DataFrame]

    return DataFramePropParser


def get_props(df: DataFrame, **kwargs) -> Dict[str, Any]:
    props = get_prop_getter(df).get_props(df, **kwargs)
    return props
