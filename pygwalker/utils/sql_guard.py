"""Validate SQL submitted to a PyGWalker data parser before it reaches an engine."""

from __future__ import annotations

from typing import Collection, Iterator

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import traverse_scope

from pygwalker.errors import UnsafeSqlError
from pygwalker.utils.custom_sqlglot import DuckdbDialect


def _expression_types(names: str) -> tuple:
    return tuple(cls for name in names.split() if (cls := getattr(exp, name, None)) is not None)


_SET_OPERATIONS = _expression_types("SetOperation Union Intersect Except")
_QUERY_TYPES = (exp.Select, exp.Subquery, *_SET_OPERATIONS)
_FORBIDDEN_NODES = _expression_types(
    "Insert Update Delete Merge Create Drop Alter Copy Attach Detach Pragma Set Use Command LoadData "
    "Transaction Commit Rollback Grant Revoke TruncateTable Analyze Cache Uncache Export Summarize "
    "Describe Show Call Execute Into File TableFromRows Lock QueryTransform"
)
_FORBIDDEN_PREFIXES = tuple(
    "read_ write_ copy_ duckdb_ pragma_ sqlite_ postgres_ mysql_ iceberg_ delta_ parquet_ csv_ "
    "json_read http_ s3_ azure_ gcs_ sniff_ st_read pg_read_ pg_ls_ pg_stat_ pg_file_ dblink_ "
    "lo_import lo_export xp_ sp_".split()
)
_FORBIDDEN_FUNCTIONS = frozenset(
    "glob load_file current_setting set_config getenv query query_table raw_sql eval exec system "
    "shell attach detach install load reflect java_method dblink query_to_xml load_extension "
    "fts3_tokenizer readfile writefile pg_execute_server_program pg_terminate_backend "
    "pg_cancel_backend pg_reload_conf pg_rotate_logfile".split()
)


def _is_forbidden_function(node: exp.Func) -> bool:
    names = (node.name,) if isinstance(node, exp.Anonymous) else (node.sql_name(), type(node).__name__)
    return any(name.lower() in _FORBIDDEN_FUNCTIONS or name.lower().startswith(_FORBIDDEN_PREFIXES) for name in names)


def iter_source_tables(ast: exp.Expression) -> Iterator[exp.Table]:
    """Yield base tables, excluding references to CTEs visible in each query scope."""
    cte_tables = set()
    if ast.find(exp.CTE):
        for scope in traverse_scope(ast):
            for table in scope.tables:
                if not table.db and not table.catalog and table.name in scope.cte_sources:
                    cte_tables.add(id(table))
    for table in ast.find_all(exp.Table):
        if id(table) not in cte_tables:
            yield table


def validate_read_only_sql(
    sql: str, *, allowed_tables: Collection[str], dialect: str = "duckdb", require_allowed_table: bool = False
) -> exp.Expression:
    """Return the single validated query, or raise UnsafeSqlError before execution."""
    if not isinstance(sql, str) or not sql.strip():
        raise UnsafeSqlError("Expected a non-empty SQL query.")
    try:
        statements = sqlglot.parse(sql, read=DuckdbDialect if dialect == "duckdb" else dialect)
    except SqlglotError as exc:
        raise UnsafeSqlError("Invalid SQL query.") from exc

    if len(statements) != 1 or not isinstance(statements[0], _QUERY_TYPES):
        raise UnsafeSqlError("Expected one read-only query.")
    ast = statements[0]
    for node in ast.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            raise UnsafeSqlError("Unsupported SQL operation.")
        if isinstance(node, (exp.Subquery, exp.CTE, *_SET_OPERATIONS)) and not isinstance(node.this, _QUERY_TYPES):
            raise UnsafeSqlError("Expected a read-only subquery.")
        if isinstance(node, _SET_OPERATIONS) and not isinstance(node.expression, _QUERY_TYPES):
            raise UnsafeSqlError("Expected a read-only set operation.")
        if isinstance(node, (exp.From, exp.Join)):
            source = node.this
            if isinstance(source, exp.Alias):
                source = source.this
            if not isinstance(source, (exp.Table, exp.Subquery)):
                raise UnsafeSqlError("Unsupported SQL data source.")
        if isinstance(node, exp.Table):
            if node.catalog or node.db or not isinstance(node.this, exp.Identifier):
                raise UnsafeSqlError("Expected an unqualified table name.")
            # SQLGlot can normalize a string literal in FROM into a quoted Identifier.
            start = node.this.meta.get("start")
            if start is not None and sql[start : start + 1] == "'":
                raise UnsafeSqlError("String literals cannot be table sources.")
        if isinstance(node, exp.Func) and _is_forbidden_function(node):
            raise UnsafeSqlError("Unsupported SQL function.")
    sources = {table.name for table in iter_source_tables(ast)}
    if sources.difference(allowed_tables):
        raise UnsafeSqlError("Table is outside the query's allowed sources.")
    if require_allowed_table and not sources:
        raise UnsafeSqlError("Query must reference an allowed table.")
    return ast
