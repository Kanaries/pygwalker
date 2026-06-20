import os.path
import subprocess
import sys

from sqlalchemy import create_engine
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from pygwalker.services.data_parsers import get_dataset_hash, get_parser
from pygwalker.data_parsers.database_parser import Connector, DatabaseDataParser, text
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
    {"fid": "name", "name": "name", "semanticType": "nominal", "analyticType": "dimension"},
    {"fid": "count", "name": "count", "semanticType": "quantitative", "analyticType": "dimension"},
    {"fid": "date", "name": "date", "semanticType": "nominal", "analyticType": "dimension"},
]
to_records_result = [{"name": "padnas", "count": 3, "date": "2022-01-01"}]
to_records_no_kernel_result = [{"name": "padnas", "count": 3, "date": "2022-01-01"}]


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


def test_data_parser_on_pyarrow_table():
    table = pa.table({key: [row[key] for row in datas] for key in datas[0]})
    dataset_parser = get_parser(table)

    assert dataset_parser.dataset_type == "pyarrow_table"
    assert dataset_parser.get_datas_by_sql(sql) == sql_result
    assert dataset_parser.raw_fields == raw_fields_result
    assert dataset_parser.to_records(1) == to_records_result
    assert get_dataset_hash(table) == get_dataset_hash(table)


@pytest.mark.parametrize(
    "dataset",
    [
        pd.DataFrame({"city": pd.Series(dtype="object"), "value": pd.Series(dtype="int64")}),
        pl.DataFrame({"city": pl.Series([], dtype=pl.String), "value": pl.Series([], dtype=pl.Int64)}),
        pa.table({"city": pa.array([], type=pa.string()), "value": pa.array([], type=pa.int64())}),
    ],
)
def test_data_parser_accepts_empty_tabular_inputs(dataset):
    dataset_parser = get_parser(dataset)

    assert dataset_parser.data_size == 0
    assert dataset_parser.to_records() == []
    assert dataset_parser.raw_fields == [
        {"fid": "city", "name": "city", "semanticType": "nominal", "analyticType": "dimension"},
        {"fid": "value", "name": "value", "semanticType": "quantitative", "analyticType": "dimension"},
    ]


def test_get_parser_reports_supported_inputs_for_unsupported_dataset():
    with pytest.raises(TypeError) as exc_info:
        get_parser(object())

    message = str(exc_info.value)
    assert "Unsupported dataset type: builtins.object" in message
    assert "pandas.DataFrame" in message
    assert "pyarrow.Table" in message
    assert "pygwalker.data_parsers.database_parser.Connector" in message
    assert "cloud dataset id string" in message


@pytest.mark.parametrize(
    "module_name",
    [
        "pygwalker.data_parsers.base",
        "pygwalker.services.render_manager",
    ],
)
def test_duckdb_import_failure_has_actionable_message(module_name):
    repo_root = os.path.dirname(os.path.dirname(__file__))
    code = f"""
import builtins
import importlib

original_import = builtins.__import__

def blocked_import(name, *args, **kwargs):
    if name == "duckdb" or name.startswith("duckdb."):
        raise ModuleNotFoundError("No module named 'duckdb'")
    return original_import(name, *args, **kwargs)

builtins.__import__ = blocked_import
importlib.import_module({module_name!r})
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "PyGWalker requires duckdb for dataframe querying" in result.stderr
    assert "pip install duckdb" in result.stderr


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

    def test_data_parser_accepts_empty_modin_input():
        df = mpd.DataFrame({"city": [], "value": []})
        dataset_parser = get_parser(df)

        assert dataset_parser.data_size == 0
        assert dataset_parser.to_records() == []
        assert dataset_parser.raw_fields == [
            {"fid": "city", "name": "city", "semanticType": "nominal", "analyticType": "dimension"},
            {"fid": "value", "name": "value", "semanticType": "nominal", "analyticType": "dimension"},
        ]

    def test_data_parser_infers_modin_series_by_position_not_label():
        df = mpd.DataFrame({"date": ["2022-01-01"]}, index=[10])
        dataset_parser = get_parser(df, infer_string_to_date=True)

        assert dataset_parser.raw_fields == [
            {"fid": "date", "name": "date", "semanticType": "temporal", "analyticType": "dimension"},
        ]
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
    view_sql = "SELECT 1"
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
        result = connector.query_datas("SELECT COUNT(1) count FROM test_datas")
        assert result[0]["count"] == data_count
        assert connector.dialect_name == "duckdb"
        assert connector.view_sql == view_sql
        assert connector.url == database_url


def test_database_parser_get_datas_by_sql_queries_connector_view():
    engine = create_engine("duckdb:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE test_datas AS SELECT 1 AS id, 'London' AS city UNION ALL SELECT 2, 'Tokyo'"))
        connector = Connector.from_sqlalchemy_connection(conn, "SELECT * FROM test_datas")
        parser = DatabaseDataParser(connector, [], False, True, {})

        assert parser.get_datas_by_sql("SELECT city FROM ___pygwalker_temp_view_name___ WHERE id = 2") == [
            {"city": "Tokyo"}
        ]
        assert parser.batch_get_datas_by_sql(
            [
                "SELECT COUNT(1) AS total FROM ___pygwalker_temp_view_name___",
                "SELECT city FROM ___pygwalker_temp_view_name___ WHERE id = 1",
            ]
        ) == [[{"total": 2}], [{"city": "London"}]]
