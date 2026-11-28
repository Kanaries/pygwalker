from concurrent.futures import ThreadPoolExecutor
import gc
import pickle
import weakref
from unittest.mock import Mock

import duckdb
import pandas as pd
import polars as pl
import pytest

from pygwalker.errors import SqlSandboxError, UnsafeSqlError
from pygwalker.api.pygwalker import PygWalker
from pygwalker.services.data_parsers import get_parser


TABLE = "pygwalker_mid_table"


@pytest.fixture
def sandbox_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".tmp").mkdir()
    (tmp_path / "input.csv").write_text("val\n1\n")
    return tmp_path


def external_queries(directory):
    return [
        f"COPY {TABLE} TO '{directory / 'output.csv'}'",
        f"COPY {TABLE} TO '.tmp/output.csv'",
        "SELECT * FROM read_text('input.csv')",
        "SELECT * FROM read_csv_auto('input.csv')",
        "SELECT * FROM glob('.tmp/*')",
        "INSTALL './local.duckdb_extension'",
        "ATTACH 'attached.db'",
        "SET enable_external_access = true",
        "SET lock_configuration = false",
    ]


def assert_sandbox_files_intact(directory):
    assert {p.relative_to(directory).as_posix() for p in directory.rglob("*")} == {".tmp", "input.csv"}
    assert (directory / "input.csv").read_text() == "val\n1\n"


@pytest.mark.parametrize("make_frame", [pd.DataFrame, pl.DataFrame])
def test_parser_rejects_external_operations(make_frame, sandbox_files):
    parser = get_parser(make_frame({"val": [1]}))
    other_dataframe = pd.DataFrame({"val": [2]})
    for sql in [*external_queries(sandbox_files), "SELECT * FROM other_dataframe"]:
        with pytest.raises(UnsafeSqlError):
            parser.get_datas_by_sql(sql)
    assert other_dataframe.val.tolist() == [2]
    assert parser._duckdb_conn is None
    assert_sandbox_files_intact(sandbox_files)


def test_private_connection_blocks_external_operations_without_guard(sandbox_files):
    parser = get_parser(pd.DataFrame({"val": [1]}))
    with parser._duckdb_lock:
        con = parser._get_duckdb_conn()
        for query in external_queries(sandbox_files):
            with pytest.raises(duckdb.Error, match="(?i)disabled|locked|permission|external access"):
                con.execute(query).fetchall()
        assert con.execute(f"SELECT val FROM {TABLE}").fetchall() == [(1,)]
    assert_sandbox_files_intact(sandbox_files)


def test_concurrent_queries_use_each_parsers_dataframe():
    parsers = [get_parser(pd.DataFrame({"val": [i]})) for i in range(2)]

    def query(i):
        return parsers[i % 2].get_datas_by_sql(f"SELECT val, {i} AS request FROM {TABLE}")

    with ThreadPoolExecutor(max_workers=6) as executor:
        assert list(executor.map(query, range(40))) == [[{"val": i % 2, "request": i}] for i in range(40)]
    assert parsers[0]._duckdb_conn is not parsers[1]._duckdb_conn


def test_parser_does_not_register_or_lock_the_global_connection():
    def global_state():
        return duckdb.query(
            f"SELECT current_setting('enable_external_access'), current_setting('lock_configuration'), "
            f"(SELECT count(*) FROM duckdb_views() WHERE view_name = '{TABLE}')"
        ).fetchone()

    before = global_state()
    parser = get_parser(pd.DataFrame({"val": [3]}))
    assert parser.get_datas_by_sql(f"SELECT val FROM {TABLE}") == [{"val": 3}]
    assert parser.field_metas == [{"key": "val", "type": "number"}]
    assert global_state() == before
    assert before == (True, False, 0)


@pytest.mark.parametrize("failure", ["connect", "timezone", "temp_directory", "register", "external_access", "lock"])
def test_failed_initialization_closes_connection_and_skips_query(monkeypatch, failure):
    parser = get_parser(pd.DataFrame({"val": [1]}))
    con = Mock()
    connect = Mock(return_value=con)
    monkeypatch.setattr(duckdb, "connect", connect)
    error = RuntimeError("sandbox initialization failed")
    if failure == "connect":
        connect.side_effect = error
    elif failure == "register":
        con.register.side_effect = error
    else:
        settings = ["timezone", "temp_directory", "external_access", "lock"]
        con.execute.side_effect = [None] * settings.index(failure) + [error]
    # Even failure during cleanup must leave the original sandbox failure visible.
    con.close.side_effect = RuntimeError("close failed")
    sql = f"SELECT val FROM {TABLE}"
    with pytest.raises(SqlSandboxError) as raised:
        parser.get_datas_by_sql(sql)
    assert raised.value.__cause__ is error
    assert all(call.args != (sql,) for call in con.execute.call_args_list)
    assert parser._duckdb_conn is None
    assert parser._duckdb_finalizer is None
    if failure != "connect":
        con.close.assert_called_once_with()


def _build_walker(parser, monkeypatch):
    monkeypatch.setattr(PygWalker, "_get_data_parser", lambda *args, **kwargs: parser)
    monkeypatch.setattr("pygwalker.api.pygwalker.check_update", lambda: None)
    return PygWalker(
        dataset=None, gid="warmup", field_specs=[], spec="", source_invoke_code="", theme_key="g2",
        appearance="media", show_cloud_tool=False, use_preview=False, kernel_computation=True,
        cloud_computation=False, use_save_tool=False, is_export_dataframe=False,
        kanaries_api_key="", default_tab="vis", gw_mode="explore",
    )


def test_warming_a_dataframe_propagates_sandbox_failure(monkeypatch):
    parser = get_parser(pd.DataFrame({"val": [1]}))
    monkeypatch.setattr(duckdb, "connect", Mock(side_effect=RuntimeError("sandbox unavailable")))
    with pytest.raises(SqlSandboxError):
        _build_walker(parser, monkeypatch)
    assert parser._duckdb_conn is None


def test_warming_skips_connector(monkeypatch):
    parser = Mock(dataset_type="connector_duckdb", raw_fields=[], data_size=0)
    _build_walker(parser, monkeypatch)
    parser.get_datas_by_sql.assert_not_called()


def test_registration_is_lazy_and_uses_the_final_dataframe():
    parser = get_parser(pd.DataFrame({"val": [1]}))
    assert parser._duckdb_conn is None
    # Modin installs its pandas representation after the base constructor returns.
    parser._duckdb_df = pd.DataFrame({"val": [2]})
    assert parser.get_datas_by_sql(f"SELECT val FROM {TABLE}") == [{"val": 2}]


def test_close_and_pickle_release_native_state():
    parser = get_parser(pd.DataFrame({"val": [1]}))
    parser.close()
    assert parser.field_metas == [{"key": "val", "type": "number"}]
    con = parser._duckdb_conn
    finalizer = parser._duckdb_finalizer
    restored = pickle.loads(pickle.dumps(parser))
    assert restored._duckdb_conn is None
    assert restored._duckdb_finalizer is None
    assert restored._duckdb_lock is not parser._duckdb_lock
    parser.close()
    parser.close()
    assert not finalizer.alive
    assert parser._duckdb_conn is parser._duckdb_finalizer is None
    with pytest.raises(duckdb.Error, match="(?i)closed"):
        con.execute("SELECT 1")
    assert restored.get_datas_by_sql(f"SELECT * FROM {TABLE}") == [{"val": 1}]


def test_gc_closes_connection_and_releases_registered_dataframe():
    parser = get_parser(pd.DataFrame({"val": [1]}))
    assert parser.get_datas_by_sql(f"SELECT * FROM {TABLE}") == [{"val": 1}]
    con = parser._duckdb_conn
    assert parser.field_metas and parser.raw_fields
    refs = [weakref.ref(obj) for obj in (parser, parser.origin_df, parser._duckdb_df)]
    del parser
    gc.collect()
    assert all(ref() is None for ref in refs)
    with pytest.raises(duckdb.Error, match="(?i)closed"):
        con.execute("SELECT 1")
