from typing import Any, Dict, List, Optional
import io

import pandas as pd

from .base import (
    BaseDataFrameDataParser,
    is_temporal_field,
    is_geo_field
)
from pygwalker.services.fname_encodings import rename_columns


class PandasDataFrameDataParser(BaseDataFrameDataParser[pd.DataFrame]):
    """prop parser for pandas.DataFrame"""

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        df = self.df[:limit] if limit is not None else self.df
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.to_csv(content, index=False)
        return content

    def to_parquet(self) -> io.BytesIO:
        content = io.BytesIO()
        self.df.to_parquet(content, index=False, compression="snappy")
        return content

    def _rename_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.reset_index(drop=True)
        df.columns = rename_columns(list(df.columns))
        return df

    def _infer_semantic(self, s: pd.Series, field_name: str):
        example_value = s[0]
        kind = s.dtype.kind

        if kind in "fcmiu" or is_geo_field(field_name):
            return "quantitative"
        if kind in "M" or (kind in "bOSUV" and is_temporal_field(example_value, self.infer_string_to_date)):
            return 'temporal'

        return "nominal"

    def _infer_analytic(self, s: pd.Series, field_name: str):
        kind = s.dtype.kind

        if is_geo_field(field_name):
            return "dimension"

        if self.infer_number_to_dimension and kind in "iu" and len(s.unique()) <= 16:
            return "dimension"

        if kind in "fcmiu":
            return "measure"

        return "dimension"

    @property
    def dataset_tpye(self) -> str:
        return "pandas_dataframe"
