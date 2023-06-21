from typing import List, Any, Dict
import json

import polars as pl

from .base import DataFramePropParser, DataFrame
from pygwalker.utils.fname_encodings import fname_decode, fname_encode
from pygwalker._constants import BYTE_LIMIT


class PolarsDataFramePropParser(DataFramePropParser[pl.DataFrame]):
    """prop parser for polars.DataFrame"""
    @classmethod
    def limited_sample(cls, df: DataFrame) -> DataFrame:
        if len(df)*2 > BYTE_LIMIT:
            df = df.head(BYTE_LIMIT//2)
        return df

    @classmethod
    def infer_semantic(cls, s: pl.Series):
        v_cnt = len(s.value_counts())
        kind = s.dtype
        return 'quantitative' if kind in pl.NUMERIC_DTYPES and v_cnt > 16 else \
            'temporal' if kind in pl.TEMPORAL_DTYPES else \
            'nominal' if kind in [pl.Boolean, pl.Object, pl.Utf8, pl.Categorical, pl.Struct, pl.List] or v_cnt <= 2 else \
            'ordinal'

    @classmethod
    def infer_analytic(cls, s: pl.Series):
        kind = s.dtype
        return 'measure' if kind in pl.FLOAT_DTYPES | pl.DURATION_DTYPES or \
                (kind in pl.INTEGER_DTYPES and len(s.value_counts()) > 16) else \
            'dimension'

    @classmethod
    def to_records(cls, df: pl.DataFrame, **kwargs) -> List[Dict[str, Any]]:
        df = df.fill_nan(None)
        return df.to_dicts()

    @classmethod
    def to_matrix(cls, df: pl.DataFrame, **kwargs) -> List[Dict[str, Any]]:
        df = df.fill_nan(None)
        dicts = df.to_dicts()
        return {'columns': list(dicts[0].keys()), 'data': [list(d.values()) for d in dicts]}

    @classmethod
    def escape_fname(cls, df: pl.DataFrame, **kwargs) -> pl.DataFrame:
        df = df.rename({i: fname_encode(i) for i in df.columns})
        return df

    @classmethod
    def decode_fname(cls, s: pl.Series, **kwargs):
        fname = fname_decode(s.name)
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return fname
