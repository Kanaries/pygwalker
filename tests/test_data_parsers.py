import pandas as pd
import polars as pl
import pytest

from pygwalker.services.data_parsers import get_parser
from pygwalker.data_parsers.database_parser import _check_view_sql
from pygwalker.errors import ViewSqlSameColumnError

datas = [
    {"name": "padnas", "count": 3, "date": "2022-01-01"},
    {"name": "polars", "count": 1, "date": "2022-01-01"},
    {"name": "modin", "count": 4, "date": "2022-01-01"},
    {"name": "pygwalker", "count": 2, "date": "2022-01-01"},
    {"name": "pygwalker", "count": 6, "date": "2022-01-01"},
]

sql = "SELECT COUNT(1) total FROM pygwalker_mid_table"
sql_result = [{"total": 5}]
raw_fields_result = [
    {'fid': 'name', 'name': 'name', 'semanticType': 'nominal', 'analyticType': 'dimension'},
    {'fid': 'count', 'name': 'count', 'semanticType': 'quantitative', 'analyticType': 'dimension'},
    {'fid': 'date', 'name': 'date', 'semanticType': 'temporal', 'analyticType': 'dimension'}
]
to_records_result = [{'name': 'padnas', 'count': 3, 'date': '2022-01-01'}]
to_records_no_kernrl_result = [{'name': 'padnas', 'count': 3, 'date': '2022-01-01'}]


def test_data_parser_on_padnas():
    df = pd.DataFrame(datas)
    dataset_parser = get_parser(df, True)
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    dataset_parser = get_parser(df, False)
    assert dataset_parser.to_records(1) == to_records_no_kernrl_result


def test_data_parser_on_polars():
    df = pl.DataFrame(datas)
    dataset_parser = get_parser(df, True)
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    dataset_parser = get_parser(df, False)
    assert dataset_parser.to_records(1) == to_records_no_kernrl_result


try:
    from modin import pandas as mpd
    def test_data_parser_on_modin():
        df = mpd.DataFrame(datas)
        dataset_parser = get_parser(df, True)
        assert dataset_parser.get_datas_by_sql(sql) == sql_result
        assert dataset_parser.raw_fields == raw_fields_result
        assert dataset_parser.to_records(1) == to_records_result
        dataset_parser = get_parser(df, False)
        assert dataset_parser.to_records(1) == to_records_no_kernrl_result
except ImportError:
    pass


def test_check_view_sql():
    _check_view_sql("SELECT * FROM table_name")
    _check_view_sql("SELECT a.f1, b.f2 FROM a LEFT JOIN b ON a.id = b.id")
    _check_view_sql("SELECT f1, f2 FROM table_name")

    with pytest.raises(ViewSqlSameColumnError):
        _check_view_sql("SELECT f1, f1 FROM table_name")
    with pytest.raises(ViewSqlSameColumnError):
        _check_view_sql("SELECT *, f1 FROM table_name")
    with pytest.raises(ViewSqlSameColumnError):
        _check_view_sql("SELECT * FROM a left join b on a.id = b.id")
    with pytest.raises(ViewSqlSameColumnError):
        _check_view_sql("SELECT a.* FROM a left join b on a.id = b.id")
