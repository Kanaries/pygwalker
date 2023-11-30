from typing import Dict, List, Any


def get_sql_from_payload(
    table_name: str,
    payload: Dict[str, Any],
    field_meta: List[Dict[str, str]] = None
) -> str:
    try:
        from gw_dsl_parser import get_sql_from_payload as __get_sql_from_payload
    except ImportError as exc:
        raise ImportError("gw_dsl_parser is not installed, please install it first. conda users please use `pip` to install it.") from exc

    sql = __get_sql_from_payload(
        table_name,
        payload,
        field_meta
    )
    return sql
