from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlglot import exp

from pygwalker.data_parsers.database_parser import Connector, DatabaseDataParser
from pygwalker.data_parsers.spark_parser import SparkDataFrameDataParser
from pygwalker.errors import UnsafeSqlError
from pygwalker.utils.payload_to_sql import get_sql_from_payload
from pygwalker.utils.sql_guard import validate_read_only_sql


TABLE = "pygwalker_mid_table"
VIEW = "___pygwalker_temp_view_name___"


@pytest.mark.parametrize(
    "sql",
    [
        None,
        42,
        "",
        "   ",
        ";",
        "-- only a comment",
        "SELECT (",
        "SELECT 1; SELECT 2",
        f"DROP VIEW {TABLE}",
        "CREATE TABLE t(a INT)",
        f"INSERT INTO {TABLE} VALUES (1)",
        f"UPDATE {TABLE} SET val = 0",
        f"DELETE FROM {TABLE}",
        f"WITH d AS (DELETE FROM {TABLE} RETURNING *) SELECT * FROM d",
        f"COPY {TABLE} TO 'output.csv'",
        "ATTACH 'test.db'",
        "INSTALL httpfs",
        "PRAGMA version",
        "SET enable_external_access = true",
        f"SELECT * INTO target FROM {TABLE}",
        "SELECT * FROM other_table",
        "SELECT * FROM information_schema.tables",
        f"SELECT * FROM main.{TABLE}",
        f"SELECT * FROM catalog.main.{TABLE}",
        "SELECT * FROM '/etc/passwd'",
        f"SELECT * FROM '{TABLE}'",
        "SELECT * FROM read_text('/etc/passwd')",
        "SELECT * FROM glob('.tmp/*')",
        "SELECT * FROM duckdb_settings()",
        "SELECT * FROM range(1000000)",
        f"SELECT * FROM {TABLE} CROSS JOIN range(10)",
        f"SELECT * FROM {TABLE}, (VALUES (1)) AS v(x)",
        f"SELECT read_text('/etc/passwd') FROM {TABLE}",
        f"SELECT current_setting('secret_directory') FROM {TABLE}",
        f"SELECT * FROM {TABLE} WHERE EXISTS (SELECT * FROM other_table)",
        f"SELECT * FROM (WITH inner_cte AS (SELECT * FROM {TABLE}) SELECT * FROM inner_cte) sub JOIN inner_cte ON TRUE",
    ],
)
def test_rejects_unsafe_sql(sql):
    with pytest.raises(UnsafeSqlError):
        validate_read_only_sql(sql, allowed_tables={TABLE})


def test_rejects_spark_path_table():
    with pytest.raises(UnsafeSqlError):
        validate_read_only_sql("SELECT * FROM parquet.`/etc/passwd`", allowed_tables={TABLE}, dialect="spark")


@pytest.mark.parametrize(
    "sql",
    [
        f"(SELECT * FROM {TABLE})",
        f"WITH a AS (SELECT * FROM {TABLE}), b AS (SELECT * FROM a) SELECT * FROM b",
        f"WITH a AS (SELECT * FROM {TABLE}) SELECT * FROM a UNION ALL SELECT * FROM a",
        f"SELECT * FROM {TABLE} INTERSECT SELECT * FROM {TABLE}",
        f"SELECT json_extract_string(cat, '$.x'), regexp_matches(cat, 'x'), date_trunc('day', day) FROM {TABLE}",
        f"SELECT row_number() OVER (PARTITION BY cat ORDER BY val) FROM {TABLE}",
    ],
)
def test_accepts_read_only_queries(sql):
    assert isinstance(validate_read_only_sql(sql, allowed_tables={TABLE}, require_allowed_table=True), exp.Expression)


def test_constant_query_table_requirement():
    assert isinstance(validate_read_only_sql("SELECT 1", allowed_tables={TABLE}), exp.Select)
    with pytest.raises(UnsafeSqlError):
        validate_read_only_sql("SELECT 1", allowed_tables={TABLE}, require_allowed_table=True)


def test_accepts_common_analytic_functions():
    sql = f"""
        SELECT sum(val), avg(val), count(*), min(val), max(val),
               coalesce(val, 1), cast(val AS DOUBLE), date_trunc('day', day),
               strftime(day, '%Y'), strptime(cat, '%Y'), epoch(day), extract(year FROM day),
               regexp_matches(cat, 'x'), regexp_replace(cat, 'x', 'y'), substring(cat, 1, 3),
               lower(cat), upper(cat), round(val, 2), floor(val), ceil(val), abs(val),
               log(val), log10(val), ln(val), power(val, 2), sqrt(val),
               row_number() OVER w, rank() OVER w, dense_rank() OVER w,
               lag(val) OVER w, lead(val) OVER w, ntile(3) OVER w, percent_rank() OVER w,
               CASE WHEN val > 1 THEN 1 ELSE 0 END, if(val > 1, 1, 0), nullif(val, 0), concat(cat, cat),
               json_extract(cat, '$.x'), json_extract_string(cat, '$.y')
        FROM {TABLE} GROUP BY val, cat, day WINDOW w AS (ORDER BY val)
    """
    assert isinstance(validate_read_only_sql(sql, allowed_tables={TABLE}), exp.Select)


def raw_view(*fields):
    return {"type": "view", "query": [{"op": "raw", "fields": list(fields)}]}


def transform_expression(op, **params):
    return {"type": "transform", "transform": [{"key": "result", "expression": {"op": op, "as": "result", **params}}]}


@pytest.mark.parametrize(
    "workflow",
    [
        [raw_view("val", "cat")],
        [
            {
                "type": "view",
                "query": [
                    {
                        "op": "aggregate",
                        "groupBy": ["cat"],
                        "measures": [{"field": "val", "agg": "sum", "asFieldKey": "total"}],
                    }
                ],
            },
            {"type": "sort", "sort": "descending", "by": ["total"]},
        ],
        [
            {
                "type": "filter",
                "filters": [
                    {"fid": "val", "rule": {"type": "range", "value": [1, 10]}},
                    {"fid": "cat", "rule": {"type": "one of", "value": ["a", "b"]}},
                    {
                        "fid": "day",
                        "rule": {"type": "temporal range", "value": [1609459200000, 1640995200000], "offset": 0},
                    },
                ],
            },
            raw_view("cat"),
        ],
        [transform_expression("bin", params=[{"type": "field", "value": "val"}], num=5), raw_view("result")],
        *[
            [transform_expression("expr", params=[{"type": "sql", "value": expr}]), raw_view("result")]
            for expr in ["val * 2 + 1", "CASE WHEN val > 2 THEN 1 ELSE 0 END", "ROUND(val, 2)", "LOWER(cat)"]
        ],
    ],
)
def test_accepts_graphic_walker_workflows(workflow):
    fields = [{"key": "val", "type": "number"}, {"key": "cat", "type": "string"}, {"key": "day", "type": "datetime"}]
    sql = get_sql_from_payload(TABLE, {"workflow": workflow}, {TABLE: fields})
    assert isinstance(validate_read_only_sql(sql, allowed_tables={TABLE}, require_allowed_table=True), exp.Select)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1",
        "SELECT * FROM other",
        f"SELECT * FROM {VIEW} JOIN other ON TRUE",
        f"WITH {VIEW} AS (SELECT 1) SELECT * FROM {VIEW}",
    ],
)
def test_database_rejects_sql_before_querying_connector(sql):
    connector = Mock(dialect_name="duckdb", view_sql="SELECT 1 AS id")
    connector.query_datas.return_value = [{"id": 1}]
    parser = DatabaseDataParser(connector, [], False, True, {})
    connector.query_datas.reset_mock()
    with pytest.raises(UnsafeSqlError):
        parser.get_datas_by_sql(sql)
    connector.query_datas.assert_not_called()


def test_database_substitutes_trusted_view_in_from_and_join():
    with create_engine("duckdb:///:memory:").connect() as conn:
        connector = Connector.from_sqlalchemy_connection(conn, "SELECT 7 AS id")
        parser = DatabaseDataParser(connector, [], False, True, {})
        assert parser.get_datas_by_sql(f"SELECT a.id FROM {VIEW} AS a JOIN {VIEW} AS b ON a.id = b.id") == [{"id": 7}]
        assert parser.get_datas_by_sql(f"SELECT {VIEW}.id FROM {VIEW}") == [{"id": 7}]
        assert parser.get_datas_by_sql(
            f"WITH a AS (SELECT id FROM {VIEW}) SELECT a.id FROM a JOIN {VIEW} b ON a.id = b.id"
        ) == [{"id": 7}]


def test_database_rejects_cte_shadowing_a_trusted_view_source():
    connector = Mock(dialect_name="duckdb", view_sql="SELECT id FROM source_table")
    connector.query_datas.return_value = [{"id": 1}]
    parser = DatabaseDataParser(connector, [], False, True, {})
    connector.query_datas.reset_mock()
    with pytest.raises(UnsafeSqlError):
        parser.get_datas_by_sql(f"WITH source_table AS (SELECT 2 AS id) SELECT * FROM {VIEW}")
    connector.query_datas.assert_not_called()


@pytest.mark.parametrize("unsafe_stage", ["input", "transpiled"])
def test_spark_rejects_sql_before_accessing_spark(unsafe_stage, monkeypatch):
    df = Mock(columns=["val"])
    parser = SparkDataFrameDataParser(df, [], False, True, {})
    transpile = Mock(return_value=["SELECT * FROM parquet.`/etc/passwd`"])
    monkeypatch.setattr("pygwalker.data_parsers.spark_parser.sqlglot.transpile", transpile)
    sql = "SELECT * FROM other" if unsafe_stage == "input" else f"SELECT * FROM {TABLE}"
    with pytest.raises(UnsafeSqlError):
        parser.get_datas_by_sql(sql)
    if unsafe_stage == "input":
        transpile.assert_not_called()
    else:
        transpile.assert_called_once_with(sql, read="duckdb", write="spark")
    parser.df.createOrReplaceTempView.assert_not_called()
    df.sparkSession.sql.assert_not_called()


def test_spark_submits_valid_transpiled_query():
    df = Mock(columns=["val"])
    parser = SparkDataFrameDataParser(df, [], False, True, {})
    df.sparkSession.sql.return_value.collect.return_value = []
    assert parser.get_datas_by_sql(f'SELECT "val" FROM {TABLE}') == []
    parser.df.createOrReplaceTempView.assert_called_once_with(TABLE)
    df.sparkSession.sql.assert_called_once_with(f"SELECT `val` FROM {TABLE}")
