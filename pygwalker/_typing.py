from typing import TypeVar, TYPE_CHECKING


dataframe_types = []
if TYPE_CHECKING:
    try:
        import pandas as pd
        dataframe_types.append(pd.DataFrame)
    except ModuleNotFoundError:
        pass
    try:
        from modin import pandas as mpd
        dataframe_types.append(mpd.DataFrame)
    except ModuleNotFoundError:
        pass
    try:
        import polars as pl
        dataframe_types.append(pl.DataFrame)
    except ModuleNotFoundError:
        pass


DataFrame = TypeVar("DataFrame", *dataframe_types)
Series = TypeVar("Series")
