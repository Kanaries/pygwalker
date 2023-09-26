from sqlglot.dialects.duckdb import DuckDB as DuckdbDialect
from sqlglot import exp
from sqlglot.helper import seq_get

DuckdbDialect.Parser.FUNCTIONS["EPOCH_MS"] = lambda args: exp.UnixToTime(
    this=exp.Div(this=seq_get(args, 0), expression=exp.Literal.number(1000.0))
)
