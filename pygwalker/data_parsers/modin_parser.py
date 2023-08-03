import json

from modin import pandas as mpd

from .base import BaseDataFrameDataParser
from pygwalker.services.fname_encodings import fname_decode, fname_encode


class ModinPandasDataFrameDataParser(BaseDataFrameDataParser[mpd.DataFrame]):
    """prop parser for pandas.DataFrame"""
    def to_records(self):
        df = self.df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    def _init_dataframe(self, df: mpd.DataFrame) -> mpd.DataFrame:
        df = df.reset_index(drop=True)
        df.columns = [f"{col}_{i+1}" for i, col in enumerate(df.columns)]
        df = df.rename(fname_encode, axis='columns')
        return df

    def _infer_semantic(self, s: mpd.Series):
        v_cnt = len(s.value_counts())
        kind = s.dtype.kind
        return 'quantitative' if (kind in 'fcmiu' and v_cnt > 16) else \
            'temporal' if kind in 'M' else \
            'nominal' if kind in 'bOSUV' or v_cnt <= 2 else \
            'ordinal'

    def _infer_analytic(self, s: mpd.Series):
        kind = s.dtype.kind
        return 'measure' if \
            kind in 'fcm' or (kind in 'iu' and len(s.value_counts()) > 16) \
                else 'dimension'

    def _decode_fname(self, s: mpd.Series):
        fname = fname_decode(s.name).rsplit('_', 1)[0]
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return fname
