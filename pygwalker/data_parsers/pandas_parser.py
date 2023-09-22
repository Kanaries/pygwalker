from typing import Any, Dict, List, Optional
import json
import io

import pandas as pd
import duckdb

from .base import (
    BaseDataFrameDataParser,
    is_temporal_field,
    is_geo_field
)
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

    def _rename_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.reset_index(drop=True)
        df.columns = [fname_encode(col) for col in rename_columns(list(df.columns))]
        return df

    def _preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def _infer_semantic(self, s: pd.Series, field_name: str):
        v_cnt = len(s.value_counts())
        example_value = s[0]
        kind = s.dtype.kind
        if (kind in "fcmiu" and v_cnt > 2) or is_geo_field(field_name):
            return "quantitative"
        if kind in "M" or (kind in "bOSUV" and is_temporal_field(str(example_value))):
            return 'temporal'
        if kind in "iu":
            return "ordinal"
        return "nominal"

    def _infer_analytic(self, s: pd.Series, field_name: str):
        kind = s.dtype.kind

        if is_geo_field(field_name):
            return "dimension"
        if kind in "fcm" or (kind in "iu" and len(s.value_counts()) > 16):
            return "measure"

        return "dimension"

    def _decode_fname(self, s: pd.Series):
        fname = fname_decode(s.name).rsplit('_', 1)[0]
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return fname
