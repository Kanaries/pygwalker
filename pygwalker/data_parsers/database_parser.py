from typing import Any, Dict, List, Optional
from functools import lru_cache
from decimal import Decimal
import logging
import json
import io

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd
import sqlglot.expressions as exp
import sqlglot

from .base import BaseDataParser, get_data_meta_type, INFINITY_DATA_SIZE
from .pandas_parser import PandasDataFrameDataParser
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.utils.custom_sqlglot import DuckdbDialect
from pygwalker.utils.payload_to_sql import get_sql_from_payload
from pygwalker.errors import ViewSqlSameColumnError

logger = logging.getLogger(__name__)


def _check_view_sql(sql: str) -> None:
    """check view sql, it will raise ViewSqlSameColumnError if view sql contain same column"""
    select_columns = [
        select.alias_or_name
        for select in sqlglot.parse_one(sql).find(exp.Select)
    ]

    has_join = sqlglot.parse_one(sql).find(exp.Join) is not None
    has_select_all = any(column == "*" for column in select_columns)
    select_expr_count = len(select_columns)
    hash_same_column = len(set(select_columns)) != select_expr_count

    if has_select_all and select_expr_count > 1:
        raise ViewSqlSameColumnError("fields with the same name may appear when use select * and select other fields")
    if has_join and has_select_all:
        raise ViewSqlSameColumnError("fields with the same name may appear when multi table join and use select *")
    if hash_same_column:
        raise ViewSqlSameColumnError("view sql can not contain same column")


class Connector:
    """
    database connector, it will cache engine by url.

    - url: database url, refer to sqlalchemy doc for url. example: mysql+pymysql://user:password@host:port/database
    - view_sql: view sql, example: SELECT * FROM table_name
    - engine_params: engine params, refer to sqlalchemy doc for params. example: {"pool_size": 10}
    """
    engine_map = {}
    JSON_TYPE_CODE_SET_MAP = {
        "snowflake": {9, 10},
        "mysql": {245}
    }
    PRE_INIT_SQL_MAP = {
        "snowflake": "ALTER SESSION SET WEEK_OF_YEAR_POLICY=1, WEEK_START=7, STRICT_JSON_OUTPUT=True;",
    }

    def __init__(self, url: str, view_sql: str, engine_params: Optional[Dict[str, Any]] = None) -> "Connector":
        _check_view_sql(view_sql)
        if engine_params is None:
            engine_params = {}

        self.url = url
        self.engine = self._get_engine(engine_params)
        self.view_sql = view_sql
        self._json_type_code_set = self.JSON_TYPE_CODE_SET_MAP.get(self.dialect_name, set())

    def _get_engine(self, engine_params: Dict[str, Any]) -> Engine:
        if self.url not in self.engine_map:
            engine = create_engine(self.url, **engine_params)
            engine.dialect.requires_name_normalize = False
            self.engine_map[self.url] = engine
            if engine.dialect.name in self.PRE_INIT_SQL_MAP:
                pre_init_sql = self.PRE_INIT_SQL_MAP[engine.dialect.name]
                with engine.connect(True) as connection:
                    connection.execute(text(pre_init_sql))

        return self.engine_map[self.url]

    def query_datas(self, sql: str) -> List[Dict[str, Any]]:
        field_type_map = {}
        with self.engine.connect() as connection:
            result = connection.execute(text(sql))
            if self.dialect_name in self.JSON_TYPE_CODE_SET_MAP:
                field_type_map = {
                    column_desc[0]: column_desc[1]
                    for column_desc in result.cursor.description
                }
            return [
                {
                    key: json.loads(value) if field_type_map.get(key, -1) in self._json_type_code_set else value
                    for key, value in item.items()
                }
                for item in result.mappings()
            ]

    @property
    def dialect_name(self) -> str:
        return self.engine.dialect.name


class DatabaseDataParser(BaseDataParser):
    """data parser for database"""
    sqlglot_dialect_map = {
        "postgresql": "postgres",
        "mssql": "tsql",
    }

    def __init__(
        self,
        conn: Connector,
        field_specs: List[FieldSpec],
        infer_string_to_date: bool,
        infer_number_to_dimension: bool,
        other_params: Dict[str, Any]
    ):
        self.conn = conn
        self.example_pandas_df = self._get_example_pandas_df()
        self.field_specs = field_specs
        self.infer_string_to_date = infer_string_to_date
        self.infer_number_to_dimension = infer_number_to_dimension
        self.other_params = other_params

    def _get_example_pandas_df(self) -> pd.DataFrame:
        sql = self._format_sql(f"SELECT * FROM {self.placeholder_table_name} LIMIT 1000")
        example_df = pd.DataFrame(self.conn.query_datas(sql))
        for column in example_df.columns:
            if any(isinstance(val, Decimal) for val in example_df[column]):
                example_df[column] = example_df[column].astype(float)
        return example_df

    def _format_sql(self, sql: str) -> str:
        sqlglot_dialect_name = self.sqlglot_dialect_map.get(self.conn.dialect_name, self.conn.dialect_name)

        sub_query = exp.Subquery(
            this=sqlglot.parse(self.conn.view_sql, read=sqlglot_dialect_name)[0],
            alias=exp.TableAlias(this="temp_view_name")
        )
        ast = sqlglot.parse(sql, read=DuckdbDialect)[0]
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
    def field_metas(self) -> List[Dict[str, str]]:
        data = self._get_datas_by_sql(f"SELECT * FROM {self.placeholder_table_name} LIMIT 1")
        return get_data_meta_type(data[0]) if data else []

    @property
    @lru_cache()
    def raw_fields(self) -> List[Dict[str, str]]:
        pandas_parser = PandasDataFrameDataParser(
            self.example_pandas_df,
            self.field_specs,
            self.infer_string_to_date,
            self.infer_number_to_dimension,
            self.other_params
        )
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
        sql = get_sql_from_payload(
            self.placeholder_table_name,
            payload,
            {self.placeholder_table_name: self.field_metas}
        )
        sql = self._format_sql(sql)
        result = self.conn.query_datas(sql)
        return result

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        pass

    def _get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        """a private method for get_datas_by_sql"""
        sql = self._format_sql(sql)
        result = self.conn.query_datas(sql)
        return result

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.example_pandas_df.toPandas().to_csv(content, index=False)
        return content

    def to_parquet(self) -> io.BytesIO:
        content = io.BytesIO()
        self.example_pandas_df.toPandas().to_parquet(content, index=False, compression="snappy")
        return content

    def batch_get_datas_by_sql(self, sql_list: List[str]) -> List[List[Dict[str, Any]]]:
        """batch get records"""
        return [
            self.get_datas_by_sql(sql)
            for sql in sql_list
        ]

    def batch_get_datas_by_payload(self, payload_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """batch get records"""
        return [
            self.get_datas_by_payload(payload)
            for payload in payload_list
        ]

    @property
    def dataset_type(self) -> str:
        return f"connector_{self.conn.dialect_name}"

    @property
    def data_size(self) -> int:
        return INFINITY_DATA_SIZE
