from typing import List, Dict, Any

import duckdb

from pygwalker._typing import DataFrame


def get_datas_from_dataframe(df: DataFrame, sql: str) -> List[Dict[str, Any]]:
    """
    Get datas from dataframe by sql(duckdb).
    """
    mid_table_name = "__mid_df"
    sql = sql.encode('utf-8').decode('unicode_escape')
    result = duckdb.query_df(df, mid_table_name, sql)
    return [
        dict(zip(result.columns, row))
        for row in result.fetchall()
    ]
