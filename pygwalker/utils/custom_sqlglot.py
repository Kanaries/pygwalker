from sqlglot.dialects.duckdb import DuckDB as DuckdbDialect
from sqlglot.dialects.postgres import Postgres as PostgresDialect
from sqlglot import exp
from sqlglot.helper import seq_get


def _postgres_round_generator(e: exp.Round) -> str:
    e = e.copy()
    e.set("this", exp.Cast(this=e.this.pop(), to="numeric"))
    return e.sql()


DuckdbDialect.Parser.FUNCTIONS["EPOCH_MS"] = lambda args: exp.UnixToTime(
    this=exp.Div(this=seq_get(args, 0), expression=exp.Literal.number(1000.0))
)
DuckdbDialect.Parser.FUNCTIONS["LOG10"] = lambda args: exp.Log(
    this=exp.Literal(this="10", is_string=False),
    expression=seq_get(args, 0)
)

PostgresDialect.Generator.TRANSFORMS[exp.Round] = lambda _, e: _postgres_round_generator(e)
