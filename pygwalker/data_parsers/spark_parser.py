from typing import Any, Dict, List, Optional
import logging
import io

from pyspark.sql import DataFrame
import sqlglot

from .base import BaseDataParser
from .pandas_parser import PandasDataFrameDataParser
from pygwalker.services.fname_encodings import fname_encode, rename_columns
from pygwalker.data_parsers.base import FieldSpec

logger = logging.getLogger(__name__)


class SparkDataFrameDataParser(BaseDataParser):
    """prop parser for DataFrame of spark"""
    def __init__(self, df: DataFrame, use_kernel_calc: bool):
        if not df.is_cached:
            logger.warning(
                "The input dataframe is not cached, which may cause performance issues.\n"
                "If dataframe is the result of a large number of calculations before, please cache it before passing it to pygwalker.\n"
                "Pyspark cache function: `df.cache()`"
            )
        self.spark = df.sparkSession
        self.origin_df = df
        self.df = self._init_dataframe(df)
        self.example_pandas_df = df.limit(1000).toPandas()
        self.use_kernel_calc = use_kernel_calc

    def raw_fields(self, field_specs: Dict[str, FieldSpec]) -> List[Dict[str, str]]:
        pandas_parser = PandasDataFrameDataParser(self.example_pandas_df, False)
        return pandas_parser.raw_fields(field_specs)

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df.limit(limit) if limit is not None else self.df
        return [row.asDict() for row in df.collect()]

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        self.df.createOrReplaceTempView("pygwalker_mid_table")
        sql = sqlglot.transpile(sql, read="duckdb", write="spark")[0]
        result_df = self.spark.sql(sql)
        return [row.asDict() for row in result_df.collect()]

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.origin_df.toPandas().to_csv(content, index=False)
        return content

    def _init_dataframe(self, df: DataFrame) -> DataFrame:
        new_columns = [fname_encode(col) for col in rename_columns(list(df.columns))]
        return df.toDF(*new_columns)
