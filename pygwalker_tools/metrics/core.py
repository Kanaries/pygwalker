from typing import Dict, Any, Tuple, List

import sqlglot.expressions as exp
import sqlglot

METRICS_DEFINITIONS = {
    "pv": {
        "name": "pv",
        "description": "Page Views",
        "fields": ["date"],
        "dimensions": ["date"],
        "params": [],
        "depends": [],
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
        "depends": [],
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
        "depends": [],
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
        "depends": [],
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
        "depends": [],
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
    },
    "active_user": {
        "name": "active_user",
        "description": "Active User",
        "fields": ["date", "user_id"],
        "dimensions": ["date"],
        "params": ["within_active_days"],
        "depends": [],
        "sql": """
            SELECT
                DISTINCT strftime(t0."date", '%Y-%m-%d') "date", t1."user_id" "user_id"
            FROM (
                SELECT DISTINCT "___default_table___"."date" FROM "___default_table___"
            ) t0
            LEFT JOIN (
                SELECT
                    DISTINCT "date"::date "date", "user_id"
                FROM
                    "___default_table___"
            ) t1
            ON
                datediff('day', t1."date", t0."date") BETWEEN 0 AND {within_active_days}
        """
    },
    "active_user_count": {
        "name": "active_user_count",
        "description": "Active User Count",
        "fields": ["date", "user_id"],
        "dimensions": ["date"],
        "params": ["within_active_days"],
        "depends": ["active_user"],
        "sql": """
            SELECT
                "active_user"."date" "date",
                COUNT(DISTINCT "active_user"."user_id") "active_user_count"
            FROM
                "active_user"
            GROUP BY
                "active_user"."date"
        """
    },
    "user_churn_rate_base_active": {
        "name": "user_churn_rate_base_active",
        "description": "User Churn Rate Base Active",
        "fields": ["date", "user_id"],
        "dimensions": ["date"],
        "params": ["within_active_days"],
        "depends": ["active_user"],
        "sql": """
            SELECT
                "t0"."date" "date",
                -(COUNT("t1"."user_id") - COUNT("t0"."user_id")) / COUNT("t0"."user_id") "user_churn_rate"
            FROM
                "active_user" "t0"
            LEFT JOIN
                "active_user" "t1"
            ON
                datediff('day', "t0"."date"::date, "t1"."date"::date) = 1 AND
                "t0"."user_id" = "t1"."user_id"
            GROUP BY
                "t0"."date"
            HAVING
                COUNT("t1"."user_id") > 0
        """
    }
}


def _replace_table_name_to_subquery(
    origin_sql: str,
    table_query_map: List[Tuple[str, str]]
) -> str:
    """
    replace table name to subquery
    example:
    _replace_table_name_to_subquery(
        "SELECT * FROM table_name",
        [("table_name", "SELECT * FROM table_name")]
    )
    """
    origin_sql_ast = sqlglot.parse(origin_sql, read="duckdb")[0]

    for table_name, sub_query in table_query_map:
        sub_query_sql_ast = sqlglot.parse(sub_query, read="duckdb")[0]
        for from_exp in origin_sql_ast.find_all(exp.From, exp.Join):
            if str(from_exp.this.this).strip('"') == table_name:
                if str(from_exp.this.alias):
                    alias_name = from_exp.this.alias
                else:
                    alias_name = table_name
                sub_query_node = exp.Subquery(
                    this=sub_query_sql_ast,
                    alias=f'"{alias_name}"'
                )
                from_exp.this.replace(sub_query_node)

    return origin_sql_ast.sql("duckdb")


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

    for field in metrics_definition["fields"]:
        if field not in field_map:
            raise ValueError(f"Field not found: {field}, all fields: {metrics_definition['fields']}")

    used_params = {}
    for param in metrics_definition["params"]:
        if param not in params:
            raise ValueError(f"Param not found: {param}, all params: {metrics_definition['params']}")
        used_params[param] = params[param]

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

    sql = metrics_definition["sql"].format(**used_params)
    table_query_map = [
        ("___default_table___", sub_query)
    ]

    for depend in metrics_definition["depends"]:
        table_query_map.append((
            depend,
            get_metrics_sql(name=depend, field_map=field_map, params=params, origin_table_name=origin_table_name)
        ))

    sql = _replace_table_name_to_subquery(sql, table_query_map)

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
