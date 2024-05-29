from sqlglot.dialects.duckdb import DuckDB as DuckdbDialect
from sqlglot.dialects.postgres import Postgres as PostgresDialect
from sqlglot.dialects.mysql import MySQL as MysqlDialect
from sqlglot.dialects.snowflake import Snowflake as SnowflakeDialect
from sqlglot import exp
from sqlglot.helper import seq_get
from sqlglot.generator import Generator
from sqlglot.dialects.dialect import (
    build_date_delta,
    build_date_delta_with_interval,
    rename_func,
    unit_to_str
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


# temporary fix for Postgres IN clause(bin filter)
def _postgres_in_sql(self: Generator, expression: exp.In) -> str:
    expression.set("expressions", [
        exp.Array(expressions=[
            exp.cast(item, to=exp.DataType.Type.DOUBLE) if isinstance(item, exp.Literal) and item.args.get("is_string") is False else item
            for item in in_item_exp.args.get("expressions", [])
        ]) if isinstance(in_item_exp, exp.Array) else in_item_exp
        for in_item_exp in expression.args.get("expressions", [])
    ])
    return self.in_sql(expression)


def _postgres_timestamp_trunc(self: Generator, expression: exp.TimestampTrunc) -> str:
    if expression.unit.this.lower() == "isoyear":
        return self.func("to_date", self.func("to_char", expression.this, exp.Literal.string("IYYY-0001")), exp.Literal.string("IYYY-IDDD"))

    return self.func("DATE_TRUNC", unit_to_str(expression), expression.this)


def _postgres_time_to_str_sql(self: Generator, expression: exp.TimeToStr) -> str:
    if expression.args.get("format").this == "%U":
        # postgres not support non-iso week
        # current_pass_days = EXTRACT(isodow FROM DATE_TRUNC('year', date))
        # week_number = floor((EXTRACT(day from date) + current_pass_days - 1) / 7)
        return self.sql(exp.Floor(
            this=exp.Div(
                this=exp.Paren(this=exp.Add(
                    this=exp.Sub(
                        this=exp.Cast(this=self.func("TO_CHAR", expression.this, exp.Literal.string("DDD")), to="int"),
                        expression=exp.Literal.number(1)
                    ),
                    expression=exp.Extract(this=exp.Var(this="isodow"), expression=exp.TimestampTrunc(this=expression.this, unit=exp.Literal.string("year")))
                )),
                expression=exp.Literal.number(7),
            )
        ))

    return self.func("TO_CHAR", expression.this, self.format_time(expression))


def _postgres_str_to_time_sql(self: Generator, expression: exp.StrToTime) -> str:
    # adapter duckdb non-iso week
    if expression.args.get("format").this == "%Y%U" and isinstance(expression.this, exp.TimeToStr) and expression.this.args.get("format").this == "%Y%U":
        return self.sql(exp.Sub(
            this=exp.TimestampTrunc(this=expression.this.this, unit=exp.Literal.string("day")),
            expression=exp.Mul(
                this=exp.Extract(this=exp.Var(this="dow"), expression=expression.this.this),
                expression=exp.Interval(this=exp.Literal.number(1), unit=exp.Var(this="day"))
            )
        ))
    return self.func("TO_TIMESTAMP", expression.this, self.format_time(expression))


def _postgres_regexp_like_sql(self: Generator, expression: exp.RegexpLike) -> str:
    flag = expression.args.get("flag")
    if flag and flag.this == "i":
        return self.binary(expression, "~*")
    return self.binary(expression, "~")


PostgresDialect.Generator.TRANSFORMS[exp.Round] = lambda _, e: _postgres_round_generator(e)
PostgresDialect.Generator.TRANSFORMS[exp.UnixToTime] = _postgres_unix_to_time_sql
PostgresDialect.Generator.TRANSFORMS[exp.In] = _postgres_in_sql
PostgresDialect.Generator.TRANSFORMS[exp.TimestampTrunc] = _postgres_timestamp_trunc
PostgresDialect.Generator.TRANSFORMS[exp.TimeToStr] = _postgres_time_to_str_sql
PostgresDialect.Generator.TRANSFORMS[exp.StrToTime] = _postgres_str_to_time_sql
PostgresDialect.Generator.TRANSFORMS[exp.RegexpLike] = _postgres_regexp_like_sql


# Mysql Dialect
def _mysql_timestamptrunc_sql(self: Generator, expression: exp.TimestampTrunc) -> str:
    unit = expression.args.get("unit")

    if unit.this.lower() == "isoyear":
        unit = exp.Var(this="YEAR")

    start_ts = "'0006-01-01 00:00:00'"

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
    if unit == "isoyear":
        return self.sql(exp.Floor(this=exp.Div(this=self.func("YEARWEEK", expression.expression, exp.Literal.number(3)), expression=exp.Literal.number(100))))
    if unit == "isodow":
        return self.sql(exp.Add(
            this=exp.Mod(this=exp.Add(this=self.func("DAYOFWEEK", expression.expression), expression=exp.Literal.number(5)), expression=exp.Literal.number(7)),
            expression=exp.Literal.number(1)
        ))
    return self.extract_sql(expression)


def _mysql_unix_to_time_sql(self: Generator, expression: exp.UnixToTime) -> str:
    scale = expression.args.get("scale") or exp.UnixToTime.SECONDS
    timestamp = expression.this

    return self.func("FROM_UNIXTIME", exp.Div(this=timestamp, expression=exp.func("POW", 10, scale)), self.format_time(expression))


def _mysql_str_to_time_sql(self: Generator, expression: exp.StrToTime) -> str:
    # adapter duckdb non-iso week
    if expression.args.get("format").this == "%Y%U" and isinstance(expression.this, exp.TimeToStr) and expression.this.args.get("format").this == "%Y%U":
        return _mysql_timestamptrunc_sql(self, exp.TimestampTrunc(this=expression.this.this, unit=exp.Literal.string("WEEK")))
    return self.func("STR_TO_DATE", expression.this, self.format_time(expression))


MysqlDialect.Generator.TRANSFORMS[exp.Extract] = _mysql_extract_sql
MysqlDialect.Generator.TRANSFORMS[exp.Array] = lambda self, e: self.func("JSON_ARRAY", *e.expressions)
MysqlDialect.Generator.TRANSFORMS[exp.TimestampTrunc] = _mysql_timestamptrunc_sql
MysqlDialect.Generator.TRANSFORMS[exp.UnixToTime] = _mysql_unix_to_time_sql
MysqlDialect.Generator.TRANSFORMS[exp.Mod] = lambda self, e: self.func("MOD", e.this, e.expression)
MysqlDialect.Generator.TRANSFORMS[exp.StrToTime] = _mysql_str_to_time_sql


# Snowflake Dialect
def _snowflake_extract_sql(self: Generator, expression: exp.Extract) -> str:
    unit = expression.this.this.lower()
    if unit == "isoyear":
        return self.func("YEAROFWEEKISO", expression.expression)
    if unit == "week":
        return self.func("WEEKISO", expression.expression)
    if unit == "isodow":
        return self.func("DAYOFWEEKISO", expression.expression)
    if unit == "dow":
        return exp.Sub(this=self.func("DAYOFWEEK", expression.expression), expression=exp.Literal.number(1))
    return rename_func("DATE_PART")(self, expression)


def _snowflake_time_to_str(self: Generator, expression: exp.TimeToStr) -> str:
    if expression.args.get("format").this == "%U":
        # snowflake not support non-iso week
        # IFF(TO_CHAR(TO_TIMESTAMP_TZ(TO_CHAR(date, 'YYYY'), 'YYYY'), 'DY') = 'Sun', WEEK(date), WEEK(date)-1)
        return self.func(
            "IFF",
            exp.EQ(
                this=self.func("TO_CHAR", self.func("TO_TIMESTAMP_TZ", self.func("TO_CHAR", expression.this, exp.Literal.string('YYYY')), exp.Literal.string('YYYY')), exp.Literal.string("DY")),
                expression=exp.Literal.string('Sun')
            ),
            self.func("WEEK", expression.this),
            exp.Sub(this=self.func("WEEK", expression.this), expression=exp.Literal.number(1))
        )

    return self.func("TO_CHAR", exp.cast(expression.this, exp.DataType.Type.TIMESTAMP), self.format_time(expression))


def _snowflake_str_to_time_sql(self: Generator, expression: exp.StrToTime) -> str:
    # adapter duckdb non-iso week
    if expression.args.get("format").this == "%Y%U" and isinstance(expression.this, exp.TimeToStr) and expression.this.args.get("format").this == "%Y%U":
        return self.func("DATE_TRUNC", exp.Literal.string("WEEK"), expression.this.this)
    return self.func("TO_TIMESTAMP", expression.this, self.format_time(expression))


def _snowflake_timestamp_trunc_sql(self: Generator, expression: exp.TimestampTrunc) -> str:
    unit = expression.unit.this.lower()

    # dateadd(day, -((date_extract(DAYOFWEEKISO from date)) - 1), date_trunc('day', date))
    trunc_iso_week = self.func(
        "dateadd",
        exp.Var(this="day"),
        exp.Sub(
            this=exp.Literal.number(1),
            expression=exp.Extract(this=exp.Var(this="DAYOFWEEKISO"), expression=expression.this)
        ),
        self.func("date_trunc", exp.Literal.string("day"), expression.this)
    )

    # dateadd(week, 1-(WEEKISO(date)), trunc_iso_week)
    if unit == "isoyear":
        return self.func(
            "dateadd",
            exp.Var(this="week"),
            exp.Sub(
                this=exp.Literal.number(1),
                expression=self.func("WEEKISO", expression.this)
            ),
            trunc_iso_week
        )

    # duckdb week means "isoweek"
    if unit == "week":
        return trunc_iso_week

    return self.func("DATE_TRUNC", expression.unit, expression.this)


SnowflakeDialect.Generator.TRANSFORMS[exp.Extract] = _snowflake_extract_sql
SnowflakeDialect.Generator.TRANSFORMS[exp.TimeToStr] = _snowflake_time_to_str
SnowflakeDialect.Generator.TRANSFORMS[exp.StrToTime] = _snowflake_str_to_time_sql
SnowflakeDialect.Generator.TRANSFORMS[exp.TimestampTrunc] = _snowflake_timestamp_trunc_sql
