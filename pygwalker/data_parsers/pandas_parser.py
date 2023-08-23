from typing import Any, Dict, List, Optional
import json
import io

import pandas as pd
import duckdb

from .base import BaseDataFrameDataParser
from pygwalker.services.fname_encodings import fname_decode, fname_encode, rename_columns


class PandasDataFrameDataParser(BaseDataFrameDataParser[pd.DataFrame]):
    """prop parser for pandas.DataFrame"""

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df[:limit] if limit is not None else self.df
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        duckdb.register("pygwalker_mid_table", self.df)
        result = duckdb.query(sql)
        return [
            dict(zip(result.columns, row))
            for row in result.fetchall()
        ]

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.origin_df.to_csv(content, index=False)
        return content

    def _init_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.reset_index(drop=True)
        df.columns = [fname_encode(col) for col in rename_columns(list(df.columns))]
        return df

    def _infer_semantic(self, s: pd.Series):
        v_cnt = len(s.value_counts())
        kind = s.dtype.kind
        return 'quantitative' if (kind in 'fcmiu' and v_cnt > 16) else \
            'temporal' if kind in 'M' else \
            'nominal' if kind in 'bOSUV' or v_cnt <= 2 else \
            'ordinal'

    def _infer_analytic(self, s: pd.Series):
        kind = s.dtype.kind
        return 'measure' if \
            kind in 'fcm' or (kind in 'iu' and len(s.value_counts()) > 16) \
                else 'dimension'

    def _decode_fname(self, s: pd.Series):
        fname = fname_decode(s.name).rsplit('_', 1)[0]
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return fname
