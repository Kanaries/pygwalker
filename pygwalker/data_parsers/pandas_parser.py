from typing import List, Any
import json

import pandas as pd

from .base import DataFramePropParser, DataFrame
from pygwalker.services.fname_encodings import fname_decode, fname_encode
from pygwalker._constants import BYTE_LIMIT


class PandasDataFramePropParser(DataFramePropParser[pd.DataFrame]):
    """prop parser for pandas.DataFrame"""
    @classmethod
    def limited_sample(cls, df: DataFrame) -> DataFrame:
        if len(df)*2 > BYTE_LIMIT:
            df = df.iloc[:BYTE_LIMIT//2]
        return df

    @classmethod
    def _infer_semantic(cls, s: pd.Series):
        v_cnt = len(s.value_counts())
        kind = s.dtype.kind
        return 'quantitative' if (kind in 'fcmiu' and v_cnt > 16) else \
            'temporal' if kind in 'M' else \
            'nominal' if kind in 'bOSUV' or v_cnt <= 2 else \
            'ordinal'

    @classmethod
    def _infer_analytic(cls, s: pd.Series):
        kind = s.dtype.kind
        return 'measure' if \
            kind in 'fcm' or (kind in 'iu' and len(s.value_counts()) > 16) \
                else 'dimension'

    @classmethod
    def _series(cls, df: pd.DataFrame, i: int, col: str):
        return df.iloc[:, i]

    @classmethod
    def _to_matrix(cls, df: pd.DataFrame) -> List[List[Any]]:
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='tight')

    @classmethod
    def _decode_fname(cls, s: pd.Series):
        fname = fname_decode(s.name)
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return fname

    @classmethod
    def escape_fname(cls, df: pd.DataFrame):
        df = df.reset_index()
        df.columns = [f"{col}_{i}" for i, col in enumerate(df.columns)]
        df = df.rename(fname_encode, axis='columns')
        return df

    @classmethod
    def to_records(cls, df: pd.DataFrame):
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')
