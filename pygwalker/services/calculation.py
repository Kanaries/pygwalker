from typing import List, Dict, Any

import duckdb

from pygwalker._typing import DataFrame


def get_datas_from_dataframe(df: DataFrame, sql: str) -> List[Dict[str, Any]]:
    """
    Get datas from dataframe by sql(duckdb).
    """
    # __mid_df as as an intermediate variable of duckdb read dataframe.
    __mid_df = df
    sql = sql.encode('utf-8').decode('unicode_escape')
    result = duckdb.query(sql)

    return [
        dict(zip(result.columns, row))
        for row in result.fetchall()
    ]
