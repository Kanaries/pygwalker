from typing import Any, Dict, List, Optional
from functools import lru_cache
import logging
import io

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from gw_dsl_parser import get_sql_from_payload
import pandas as pd
import sqlglot.expressions as exp
import sqlglot

from .base import BaseDataParser
from .pandas_parser import PandasDataFrameDataParser
from pygwalker.data_parsers.base import FieldSpec

logger = logging.getLogger(__name__)


class Connector:
    """database connector"""
    def __init__(self, url: str, view_sql: str) -> "Connector":
        self.url = url
        self.engine = self._get_engine()
        self.view_sql = view_sql

    def _format_sql(self, sql: str) -> str:
        sub_query = exp.Subquery(
            this=sqlglot.parse(self.view_sql)[0],
            alias=self.view_name
        )
        ast = sqlglot.parse(sql)[0]
        ast.args["from"].this.replace(sub_query)
        return str(ast)

    def _get_engine(self) -> Engine:
        return create_engine(self.url)

    def query_datas(self, sql: str) -> List[Dict[str, Any]]:
        sql = self._format_sql(sql)
        with self.engine.connect() as connection:
            return [
                dict(item)
                for item in connection.execute(text(sql)).mappings()
            ]

    @property
    def dialect_name(self) -> str:
        return self.engine.dialect.name

    @property
    def view_name(self) -> str:
        return "pygwalker_temp_view"


class DatabaseDataParser(BaseDataParser):
    """data parser for database"""
    sqlglot_dialect_map = {
        "postgresql": "postgres"
    }

    def __init__(self, conn: Connector, _: bool, field_specs: Dict[str, FieldSpec]):
        self.conn = conn
        self.example_pandas_df = pd.DataFrame(
            self.conn.query_datas(f"SELECT * FROM {self.conn.view_name} LIMIT 1000")
        )
        self.field_specs = field_specs

    @property
    @lru_cache()
    def raw_fields(self) -> List[Dict[str, str]]:
        pandas_parser = PandasDataFrameDataParser(self.example_pandas_df, False, self.field_specs)
        return [
            {**field, "fid": field["name"]}
            for field in pandas_parser.raw_fields
        ]

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None:
            df = self.example_pandas_df
        else:
            df = self.example_pandas_df[:limit]
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        sql = get_sql_from_payload(self.conn.view_name, payload, 0)
        sqlglot_dialect_name = self.sqlglot_dialect_map.get(
            self.conn.dialect_name,
            self.conn.dialect_name
        )
        sql = sqlglot.transpile(sql, read="duckdb", write=sqlglot_dialect_name)[0]
        return self.conn.query_datas(sql)

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        return []

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.example_pandas_df.toPandas().to_csv(content, index=False)
        return content
