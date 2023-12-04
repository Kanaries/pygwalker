from typing import List, Any, Dict, Optional
import io

import polars as pl

from .base import (
    BaseDataFrameDataParser,
    is_temporal_field,
    is_geo_field
)
from pygwalker.services.fname_encodings import rename_columns


class PolarsDataFrameDataParser(BaseDataFrameDataParser[pl.DataFrame]):
    """prop parser for polars.DataFrame"""

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
        df = df.rename({
            old_col: new_col
            for old_col, new_col in zip(df.columns, rename_columns(df.columns))
        })
        return df

    def _preprocess_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        return df

    def _infer_semantic(self, s: pl.Series, field_name: str):
        v_cnt = len(s.value_counts())
        example_value = s[0]
        kind = s.dtype

        if (kind in pl.NUMERIC_DTYPES and v_cnt > 2) or is_geo_field(field_name):
            return "quantitative"
        if kind in pl.TEMPORAL_DTYPES or is_temporal_field(str(example_value)):
            return "temporal"
        if kind in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]:
            return "ordinal"
        return "nominal"

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

    @property
    def dataset_tpye(self) -> str:
        return "polars_dataframe"
