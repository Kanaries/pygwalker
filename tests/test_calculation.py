import pandas as pd
import polars as pl

from pygwalker.services.data_parsers import get_parser

datas = [
    {"name": "padnas", "count": 3},
    {"name": "polars", "count": 1},
    {"name": "modin", "count": 4},
    {"name": "pygwalker", "count": 2},
    {"name": "pygwalker", "count": 6},
]

sql = "SELECT COUNT(1) total FROM pygwalker_mid_table"
result = [{"total": 5}]


def test_calculation_on_padnas():
    df = pd.DataFrame(datas)
    assert get_parser(df, True).get_datas_by_sql(sql) == result


def test_calculation_on_polars():
    df = pl.DataFrame(datas)
    assert get_parser(df, True).get_datas_by_sql(sql) == result


try:
    from modin import pandas as mpd
    def test_calculation_on_modin():
        df = mpd.DataFrame(datas)
        assert get_parser(df, True).get_datas_by_sql(sql) == result
except ImportError:
    pass
