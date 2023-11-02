from typing import Any, Dict, List, Optional
from functools import lru_cache
from decimal import Decimal
import logging
import io

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd
import sqlglot.expressions as exp
import sqlglot

from .base import BaseDataParser
from .pandas_parser import PandasDataFrameDataParser
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.utils.custom_sqlglot import DuckdbDialect

logger = logging.getLogger(__name__)


class Connector:
    """database connector"""
    def __init__(self, url: str, view_sql: str) -> "Connector":
        self.url = url
        self.engine = self._get_engine()
        self.view_sql = view_sql

    def _get_engine(self) -> Engine:
        engine = create_engine(self.url)
        engine.dialect.requires_name_normalize = False
        return engine

    def query_datas(self, sql: str) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            return [
                dict(item)
                for item in connection.execute(text(sql)).mappings()
            ]

    @property
    def dialect_name(self) -> str:
        return self.engine.dialect.name


class DatabaseDataParser(BaseDataParser):
    """data parser for database"""
    sqlglot_dialect_map = {
        "postgresql": "postgres"
    }

    def __init__(self, conn: Connector, _: bool, field_specs: Dict[str, FieldSpec]):
        self.conn = conn
        self.example_pandas_df = self._get_example_pandas_df()
        self.field_specs = field_specs

    def _get_example_pandas_df(self) -> pd.DataFrame:
        sql = self._format_sql(f"SELECT * FROM {self.placeholder_table_name} LIMIT 1000")
        example_df = pd.DataFrame(self.conn.query_datas(sql))
        for column in example_df.columns:
            if any(isinstance(val, Decimal) for val in example_df[column]):
                example_df[column] = example_df[column].astype(float)
        return example_df

    def _format_sql(self, sql: str) -> str:
        sqlglot_dialect_name = self.sqlglot_dialect_map.get(self.conn.dialect_name, self.conn.dialect_name)
        sql = sqlglot.transpile(sql, read=DuckdbDialect, write=sqlglot_dialect_name)[0]

        sub_query = exp.Subquery(
            this=sqlglot.parse(self.conn.view_sql, read=sqlglot_dialect_name)[0],
            alias="temp_view_name"
        )
        ast = sqlglot.parse(sql, read=sqlglot_dialect_name)[0]
        for from_exp in ast.find_all(exp.From):
            if str(from_exp.this).strip('"') == self.placeholder_table_name:
                from_exp.this.replace(sub_query)

        sql = ast.sql(sqlglot_dialect_name)
        return sql

    @property
    def placeholder_table_name(self) -> str:
        return "___pygwalker_temp_view_name___"

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
        # temporary solution: wasmtime is not supported in conda
        # pylint: disable=import-outside-toplevel
        from gw_dsl_parser import get_sql_from_payload
        sql = get_sql_from_payload(self.placeholder_table_name, payload)
        sql = self._format_sql(sql)
        result = self.conn.query_datas(sql)
        return result

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        return []

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.example_pandas_df.toPandas().to_csv(content, index=False)
        return content

    @property
    def dataset_tpye(self) -> str:
        return f"connector_{self.conn.dialect_name}"
