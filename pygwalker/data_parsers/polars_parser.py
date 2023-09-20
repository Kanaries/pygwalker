from typing import List, Any, Dict, Optional
import json
import io

import polars as pl
import duckdb

from .base import (
    BaseDataFrameDataParser,
    is_temporal_field,
    is_geo_field
)
from pygwalker.services.fname_encodings import fname_decode, fname_encode, rename_columns


class PolarsDataFrameDataParser(BaseDataFrameDataParser[pl.DataFrame]):
    """prop parser for polars.DataFrame"""

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df[:limit] if limit is not None else self.df
        df = df.fill_nan(None)
        return df.to_dicts()

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        duckdb.register("pygwalker_mid_table", self.df)
        result = duckdb.query(sql)
        return [
            dict(zip(result.columns, row))
            for row in result.fetchall()
        ]

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.origin_df.write_csv(content)
        return content

    def _rename_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.rename({
            old_col: fname_encode(new_col)
            for old_col, new_col in zip(df.columns, rename_columns(df.columns))
        })
        return df

    def _preprocess_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        return df

    def _infer_semantic(self, s: pl.Series, field_name: str):
        v_cnt = len(s.value_counts())
        example_value = s[0]
        kind = s.dtype

        if (kind in pl.NUMERIC_DTYPES and v_cnt > 16) or is_geo_field(field_name):
            return "quantitative"
        if kind in pl.TEMPORAL_DTYPES or is_temporal_field(str(example_value)):
            return "temporal"
        if kind in [pl.Boolean, pl.Object, pl.Utf8, pl.Categorical, pl.Struct, pl.List] or v_cnt <= 2:
            return "nominal"
        return "ordinal"

    def _infer_analytic(self, s: pl.Series, field_name: str):
        kind = s.dtype

        if is_geo_field(field_name):
            return "dimension"
        if (
            kind in (pl.FLOAT_DTYPES | pl.DURATION_DTYPES)
            or (kind in pl.INTEGER_DTYPES and len(s.value_counts()) > 16)
        ):
            return "measure"

        return "dimension"

    def _decode_fname(self, s: pl.Series):
        fname = fname_decode(s.name).rsplit('_', 1)[0]
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return fname
