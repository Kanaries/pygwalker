from sqlglot.dialects.duckdb import DuckDB as DuckdbDialect
from sqlglot.dialects.postgres import Postgres as PostgresDialect
from sqlglot.dialects.mysql import MySQL as MysqlDialect
from sqlglot import exp
from sqlglot.helper import seq_get
from sqlglot.generator import Generator
from sqlglot.dialects.dialect import (
    build_date_delta,
    build_date_delta_with_interval,
)


# Duckdb Dialect
DuckdbDialect.Parser.FUNCTIONS["LOG10"] = lambda args: exp.Log(
    this=exp.Literal(this="10", is_string=False),
    expression=seq_get(args, 0)
)


# Postgres Dialect
def _postgres_round_generator(e: exp.Round) -> str:
    e = e.copy()
    e.set("this", exp.Cast(this=e.this.pop(), to="numeric"))
    return e.sql()


def _postgres_unix_to_time_sql(self: Generator, expression: exp.UnixToTime) -> str:
    scale = expression.args.get("scale")
    timestamp = expression.this

    if scale in (None, exp.UnixToTime.SECONDS):
        return self.func("to_timestamp", timestamp)

    return self.func("to_timestamp", exp.Div(this=timestamp, expression=exp.func("POW", 10, scale)))


PostgresDialect.Generator.TRANSFORMS[exp.Round] = lambda _, e: _postgres_round_generator(e)
PostgresDialect.Generator.TRANSFORMS[exp.UnixToTime] = _postgres_unix_to_time_sql


# Mysql Dialect
def _mysql_timestamptrunc_sql(self: Generator, expression: exp.TimestampTrunc) -> str:
    unit = expression.args.get("unit")

    start_ts = "'0001-01-01 00:00:00'"

    timestamp_diff = build_date_delta(exp.TimestampDiff)([unit, start_ts, expression.this])
    interval = exp.Interval(this=timestamp_diff, unit=unit)
    dateadd = build_date_delta_with_interval(exp.DateAdd)([start_ts, interval])

    return self.sql(dateadd)


def _mysql_extract_sql(self: Generator, expression: exp.Extract) -> str:
    unit = expression.this.this
    if unit == "dow":
        return self.sql(exp.Sub(this=self.func("DAYOFWEEK", expression.expression), expression=exp.Literal.number(1)))
    if unit == "week":
        return self.func("WEEK", expression.expression, exp.Literal.number(3))
    return self.extract_sql(expression)


def _mysql_unix_to_time_sql(self: Generator, expression: exp.UnixToTime) -> str:
    scale = expression.args.get("scale") or exp.UnixToTime.SECONDS
    timestamp = expression.this

    return self.func("FROM_UNIXTIME", exp.Div(this=timestamp, expression=exp.func("POW", 10, scale)), self.format_time(expression))


MysqlDialect.Generator.TRANSFORMS[exp.Extract] = _mysql_extract_sql
MysqlDialect.Generator.TRANSFORMS[exp.Array] = lambda self, e: self.func("JSON_ARRAY", *e.expressions)
MysqlDialect.Generator.TRANSFORMS[exp.TimestampTrunc] = _mysql_timestamptrunc_sql
MysqlDialect.Generator.TRANSFORMS[exp.UnixToTime] = _mysql_unix_to_time_sql
