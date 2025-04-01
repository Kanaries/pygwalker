import os.path

from sqlalchemy import create_engine
import pandas as pd
import polars as pl
import pytest

from pygwalker.services.data_parsers import get_parser
from pygwalker.data_parsers.database_parser import Connector, text
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
    {'fid': 'date', 'name': 'date', 'semanticType': 'nominal', 'analyticType': 'dimension'}
]
to_records_result = [{'name': 'padnas', 'count': 3, 'date': '2022-01-01'}]
to_records_no_kernel_result = [{'name': 'padnas', 'count': 3, 'date': '2022-01-01'}]


def test_data_parser_on_padnas():
    df = pd.DataFrame(datas)
    dataset_parser = get_parser(df)
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    dataset_parser = get_parser(df)
    assert dataset_parser.to_records(1) == to_records_no_kernel_result


def test_data_parser_on_polars():
    df = pl.DataFrame(datas)
    dataset_parser = get_parser(df)
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    dataset_parser = get_parser(df)
    assert dataset_parser.to_records(1) == to_records_no_kernel_result


try:
    from modin import pandas as mpd
    def test_data_parser_on_modin():
        df = mpd.DataFrame(datas)
        dataset_parser = get_parser(df)
        assert dataset_parser.get_datas_by_sql(sql) == sql_result
        assert dataset_parser.raw_fields == raw_fields_result
        assert dataset_parser.to_records(1) == to_records_result
        dataset_parser = get_parser(df)
        assert dataset_parser.to_records(1) == to_records_no_kernel_result
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


def test_connector():
    csv_file = os.path.join(os.path.dirname(__file__), "bike_sharing_dc.csv")
    database_url = "duckdb:///:memory:"
    view_sql = f"SELECT 1"
    data_count = 17379

    connector = Connector(database_url, view_sql)
    result = connector.query_datas(f"SELECT COUNT(1) count FROM read_csv_auto('{csv_file}')")
    assert result[0]["count"] == data_count
    assert connector.dialect_name == "duckdb"
    assert connector.view_sql == view_sql
    assert connector.url == database_url

    engine = create_engine(database_url)
    connector = Connector.from_sqlalchemy_engine(engine, view_sql)
    result = connector.query_datas(f"SELECT COUNT(1) count FROM read_csv_auto('{csv_file}')")
    assert result[0]["count"] == data_count
    assert connector.dialect_name == "duckdb"
    assert connector.view_sql == view_sql
    assert connector.url == database_url

    engine = create_engine(database_url)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE TABLE test_datas AS SELECT * FROM read_csv_auto('{csv_file}')"))
        connector = Connector.from_sqlalchemy_connection(conn, view_sql)
        result = connector.query_datas(f"SELECT COUNT(1) count FROM test_datas")
        assert result[0]["count"] == data_count
        assert connector.dialect_name == "duckdb"
        assert connector.view_sql == view_sql
        assert connector.url == database_url
