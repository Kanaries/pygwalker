from typing import Dict, Any

import sqlglot.expressions as exp
import sqlglot

METRICS_DEFINITIONS = {
    "pv": {
        "name": "pv",
        "description": "Page Views",
        "fields": ["date"],
        "dimensions": ["date"],
        "params": [],
        "sql": """
            SELECT
                strftime("date", '%Y-%m-%d') "date",
                COUNT(1) "pv"
            FROM
                "___default_table___"
            GROUP BY
                strftime("date", '%Y-%m-%d')
        """
    },
    "uv": {
        "name": "uv",
        "description": "User Views",
        "fields": ["date", "user_id"],
        "dimensions": ["date"],
        "params": [],
        "sql": """
            SELECT
                strftime("date", '%Y-%m-%d') "date",
                COUNT(DISTINCT "user_id") "uv"
            FROM
                "___default_table___"
            GROUP BY
                strftime("date", '%Y-%m-%d')
        """
    },
    "mau": {
        "name": "mau",
        "description": "Monthly Active Users",
        "fields": ["date", "user_id"],
        "dimensions": ["date"],
        "params": [],
        "sql": """
            SELECT
                strftime("date", '%Y-%m') "date",
                COUNT(DISTINCT "user_id") "mau"
            FROM
                "___default_table___"
            GROUP BY
                strftime("date", '%Y-%m')
        """
    },
    "retention": {
        "name": "retention",
        "description": "Retention",
        "fields": ["date", "user_id", "user_signup_date"],
        "dimensions": ["date"],
        "params": ["time_unit", "time_size"],
        "sql": """
            SELECT
                strftime(t0."date", '%Y-%m-%d') "date",
                COUNT(DISTINCT t1."user_id") / COUNT(DISTINCT t0."user_id") "retention"
            FROM (
                SELECT
                    DISTINCT "date"::date "date", "user_id"
                FROM
                    "___default_table___"
                WHERE
                    "date"::date = "user_signup_date"::date
            ) t0
            LEFT JOIN (
                SELECT
                    DISTINCT "date"::date "date", "user_id"
                FROM
                    "___default_table___"
            ) t1
            ON
                t0."user_id" = t1."user_id" AND
                t0."date" < t1."date" AND
                datediff('{time_unit}', t0."date", t1."date") = {time_size}
            GROUP BY
                strftime(t0."date", '%Y-%m-%d')
        """
    },
    "new_user_count": {
        "name": "new_user_count",
        "description": "New User Count",
        "fields": ["date", "user_id", "user_signup_date"],
        "dimensions": ["date"],
        "params": [],
        "sql": """
            SELECT
                strftime("___default_table___"."date", '%Y-%m-%d') "date",
                COUNT(DISTINCT "___default_table___"."user_id") "new_user_count"
            FROM
                "___default_table___"
            WHERE
                "date"::date = "user_signup_date"::date
            GROUP BY
                strftime("___default_table___"."date", '%Y-%m-%d')
        """
    }
}


def get_metrics_sql(
    *,
    name: str,
    field_map: Dict[str, str],
    params: Dict[str, Any],
    origin_table_name: str
) -> str:
    """get metrics sql"""
    if name not in METRICS_DEFINITIONS:
        raise ValueError(f"Unknown metrics name: {name}")
    metrics_definition = METRICS_DEFINITIONS[name]

    if set(metrics_definition["fields"]) != set(field_map.keys()):
        raise ValueError(f"Fields not match: {metrics_definition['fields']}")

    if set(metrics_definition["params"]) != set(params.keys()):
        raise ValueError(f"Params not match: {metrics_definition['params']}")

    timestamp_field = {"date"}

    field_map_sql = ",\n".join([
        f'"{field_map[field]}" "{field}"' if field not in timestamp_field else f'"{field_map[field]}"::timestamp "{field}"'
        for field in metrics_definition["fields"]
    ])
    sub_query = f"""
        SELECT
            {field_map_sql}
        FROM
            "{origin_table_name}"
    """

    origin_sql_ast = sqlglot.parse(sub_query, read="duckdb")[0]
    sub_query_node = exp.Subquery(
        this=origin_sql_ast,
        alias="___default_table___"
    )

    sql_str = metrics_definition["sql"].format(**params)
    sql_ast = sqlglot.parse(sql_str, read="duckdb")[0]
    for from_exp in sql_ast.find_all(exp.From, exp.Join):
        if str(from_exp.this.this).strip('"') == "___default_table___":
            if str(from_exp.this.alias):
                alias_name = from_exp.this.alias
            else:
                alias_name = "___default_table___"
            sub_query_node = exp.Subquery(
                this=origin_sql_ast,
                alias=f'"{alias_name}"'
            )
            from_exp.this.replace(sub_query_node)

    sql = sql_ast.sql("duckdb")

    return sql


def get_help_text() -> str:
    """get help text"""
    help_text = "Available metrics:\n"

    for metrics_item in METRICS_DEFINITIONS.values():
        help_text += (
            f"  - {metrics_item['name']}: {metrics_item['description']}\n"
            f"    - fields: {metrics_item['fields']}\n"
            f"    - dimensions: {metrics_item['dimensions']}\n"
            f"    - params: {metrics_item['params']}\n"
        )

    return help_text
