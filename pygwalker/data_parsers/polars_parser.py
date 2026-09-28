from typing import List, Any, Dict, Optional
from functools import cached_property
import io

import polars as pl

from .base import BaseDataFrameDataParser, is_temporal_field, is_geo_field
from pygwalker.services.fname_encodings import rename_columns
from pygwalker.utils.payload_to_sql import get_sql_from_payload


def _is_numeric_dtype(dtype: pl.DataType) -> bool:
    is_numeric = getattr(dtype, "is_numeric", None)
    if is_numeric is not None:
        return is_numeric()
    return dtype in pl.NUMERIC_DTYPES


def _is_integer_dtype(dtype: pl.DataType) -> bool:
    is_integer = getattr(dtype, "is_integer", None)
    if is_integer is not None:
        return is_integer()
    return dtype in pl.INTEGER_DTYPES


def _is_temporal_dtype(dtype: pl.DataType) -> bool:
    is_temporal = getattr(dtype, "is_temporal", None)
    if is_temporal is not None:
        return is_temporal()
    return dtype in pl.TEMPORAL_DTYPES


class PolarsDataFrameDataParser(BaseDataFrameDataParser[pl.DataFrame]):
    """Surgically optimized property & data parser for polars.DataFrame.
    
    Bypasses all DuckDB and Pandas conversions to process queries purely using
    Polars' multi-threaded Rust SQLContext and Arrow memory backend.
    """

    @cached_property
    def field_metas(self) -> List[Dict[str, str]]:
        meta_types = []
        for col_name, dtype in self.df.schema.items():
            if _is_temporal_dtype(dtype):
                time_zone = getattr(dtype, "time_zone", None)
                field_meta_type = "datetime_tz" if time_zone else "datetime"
            elif _is_numeric_dtype(dtype):
                field_meta_type = "number"
            else:
                field_meta_type = "string"
            meta_types.append({"key": col_name, "type": field_meta_type})
        return meta_types

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query using Polars native multi-threaded SQLContext."""
        ctx = pl.SQLContext(pygwalker_mid_table=self.df.lazy())
        result_df = ctx.execute(sql, eager=True)
        result_df = result_df.fill_nan(None)
        return result_df.to_dicts()

    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        sql = get_sql_from_payload("pygwalker_mid_table", payload, {"pygwalker_mid_table": self.field_metas})
        return self.get_datas_by_sql(sql)

    def batch_get_datas_by_sql(self, sql_list: List[str]) -> List[List[Dict[str, Any]]]:
        """Batch get records using native Polars SQLContext."""
        return [self.get_datas_by_sql(sql) for sql in sql_list]

    def batch_get_datas_by_payload(self, payload_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Batch get records via payload using native Polars SQLContext."""
        return [self.get_datas_by_payload(payload) for payload in payload_list]

    @property
    def data_size(self) -> int:
        return self.df.estimated_size()

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df[:limit] if limit is not None else self.df
        df = df.fill_nan(None)
        return df.to_dicts()

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.write_csv(content)
        return content

    def to_parquet(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.write_parquet(content, compression="snappy")
        return content

    def _rename_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.rename({old_col: new_col for old_col, new_col in zip(df.columns, rename_columns(df.columns))})
        return df

    def _infer_semantic(self, s: pl.Series, field_name: str):
        kind = s.dtype

        if _is_numeric_dtype(kind) or is_geo_field(field_name):
            return "quantitative"
        if _is_temporal_dtype(kind):
            return "temporal"
        if len(s) > 0 and is_temporal_field(s[0], self.infer_string_to_date):
            return "temporal"

        return "nominal"

    def _infer_analytic(self, s: pl.Series, field_name: str):
        kind = s.dtype

        if is_geo_field(field_name):
            return "dimension"

        if self.infer_number_to_dimension and _is_integer_dtype(kind) and len(s.unique()) <= 16:
            return "dimension"

        if _is_numeric_dtype(kind):
            return "measure"

        return "dimension"

    @property
    def dataset_type(self) -> str:
        return "polars_dataframe"
