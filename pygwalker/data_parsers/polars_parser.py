from typing import List, Any, Dict
import json

import polars as pl

from .base import BaseDataFrameDataParser
from pygwalker.services.fname_encodings import fname_decode, fname_encode


class PolarsDataFrameDataParser(BaseDataFrameDataParser[pl.DataFrame]):
    """prop parser for polars.DataFrame"""
    def to_records(self) -> List[Dict[str, Any]]:
        df = self.df.fill_nan(None)
        return df.to_dicts()

    def _init_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.sample(frac=1)
        df = df.rename({i: fname_encode(i) for i in df.columns})
        return df

    def _infer_semantic(self, s: pl.Series):
        v_cnt = len(s.value_counts())
        kind = s.dtype
        return 'quantitative' if kind in pl.NUMERIC_DTYPES and v_cnt > 16 else \
            'temporal' if kind in pl.TEMPORAL_DTYPES else \
            'nominal' if kind in [pl.Boolean, pl.Object, pl.Utf8, pl.Categorical, pl.Struct, pl.List] or v_cnt <= 2 else \
            'ordinal'

    def _infer_analytic(self, s: pl.Series):
        kind = s.dtype
        return 'measure' if kind in pl.FLOAT_DTYPES | pl.DURATION_DTYPES or \
                (kind in pl.INTEGER_DTYPES and len(s.value_counts()) > 16) else \
            'dimension'

    def _to_matrix(self) -> List[Dict[str, Any]]:
        df = self.fill_nan(None)
        dicts = df.to_dicts()
        return {'columns': list(dicts[0].keys()), 'data': [list(d.values()) for d in dicts]}

    def _decode_fname(self, s: pl.Series):
        fname = fname_decode(s.name)
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return fname
