from typing import Any, Dict, List, Optional
from functools import lru_cache
import logging
import io

from pyspark.sql import DataFrame
import sqlglot

from .base import BaseDataParser, get_data_meta_type, INFINITY_DATA_SIZE
from .pandas_parser import PandasDataFrameDataParser
from pygwalker.services.fname_encodings import rename_columns
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.utils.payload_to_sql import get_sql_from_payload

logger = logging.getLogger(__name__)


class SparkDataFrameDataParser(BaseDataParser):
    """prop parser for DataFrame of spark"""
    def __init__(
        self,
        df: DataFrame,
        field_specs: List[FieldSpec],
        infer_string_to_date: bool,
        infer_number_to_dimension: bool,
        other_params: Dict[str, Any]
    ):
        if not df.is_cached:
            logger.warning(
                "The input dataframe is not cached, which may cause performance issues.\n"
                "If dataframe is the result of a large number of calculations before, please cache it before passing it to pygwalker.\n"
                "Pyspark cache function: `df.cache()`"
            )
        self.spark = df.sparkSession
        self.origin_df = df
        self.df = self._rename_dataframe(df)
        self.example_pandas_df = df.limit(1000).toPandas()
        self.field_specs = field_specs
        self.infer_string_to_date = infer_string_to_date
        self.infer_number_to_dimension = infer_number_to_dimension
        self.other_params = other_params

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
        return pandas_parser.raw_fields

    @property
    @lru_cache()
    def field_metas(self) -> List[Dict[str, str]]:
        data = self.get_datas_by_sql("SELECT * FROM pygwalker_mid_table LIMIT 1")
        return get_data_meta_type(data[0]) if data else []

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df.limit(limit) if limit is not None else self.df
        return [row.asDict() for row in df.collect()]

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        self.df.createOrReplaceTempView("pygwalker_mid_table")
        sql = sqlglot.transpile(sql, read="duckdb", write="spark")[0]
        result_df = self.spark.sql(sql)
        return [row.asDict() for row in result_df.collect()]

    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        sql = get_sql_from_payload(
            "pygwalker_mid_table",
            payload,
            {"pygwalker_mid_table": self.field_metas}
        )
        return self.get_datas_by_sql(sql)

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

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.toPandas().to_csv(content, index=False)
        return content

    def to_parquet(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.toPandas().to_parquet(content, index=False, compression="snappy")
        return content

    def _rename_dataframe(self, df: DataFrame) -> DataFrame:
        new_columns = rename_columns(list(df.columns))
        return df.toDF(*new_columns)

    @property
    def dataset_tpye(self) -> str:
        return "spark_dataframe"

    @property
    def placeholder_table_name(self) -> str:
        return "pygwalker_mid_table"

    @property
    def data_size(self) -> int:
        return INFINITY_DATA_SIZE
