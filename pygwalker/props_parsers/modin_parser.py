from typing import List, Any
import json

from modin import pandas as mpd

from .base import DataFramePropParser, DataFrame
from pygwalker.services.fname_encodings import fname_decode, fname_encode
from pygwalker._constants import BYTE_LIMIT


class ModinPandasDataFramePropParser(DataFramePropParser[mpd.DataFrame]):
    """prop parser for pandas.DataFrame"""
    @classmethod
    def limited_sample(cls, df: DataFrame) -> DataFrame:
        if len(df)*2 > BYTE_LIMIT:
            df = df.iloc[:BYTE_LIMIT//2]
        return df

    @classmethod
    def infer_semantic(cls, s: mpd.Series):
        v_cnt = len(s.value_counts())
        kind = s.dtype.kind
        return 'quantitative' if (kind in 'fcmiu' and v_cnt > 16) else \
            'temporal' if kind in 'M' else \
            'nominal' if kind in 'bOSUV' or v_cnt <= 2 else \
            'ordinal'

    @classmethod
    def infer_analytic(cls, s: mpd.Series):
        kind = s.dtype.kind
        return 'measure' if \
            kind in 'fcm' or (kind in 'iu' and len(s.value_counts()) > 16) \
                else 'dimension'

    @classmethod
    def series(cls, df: mpd.DataFrame, i: int, col: str):
        return df.iloc[:, i]

    @classmethod
    def to_records(cls, df: mpd.DataFrame):
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    @classmethod
    def to_matrix(cls, df: mpd.DataFrame, **kwargs) -> List[List[Any]]:
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='tight')

    @classmethod
    def escape_fname(cls, df: mpd.DataFrame, **kwargs):
        df = df.reset_index()
        df.columns = [f"{col}_{i}" for i, col in enumerate(df.columns)]
        df = df.rename(fname_encode, axis='columns')
        return df

    @classmethod
    def decode_fname(cls, s: mpd.Series, **kwargs):
        fname = fname_decode(s.name)
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return fname
