from typing import Any, Dict, List, Optional
from functools import lru_cache
from decimal import Decimal
import logging
import io

import pandas as pd

from .base import BaseDataParser, get_data_meta_type
from .pandas_parser import PandasDataFrameDataParser
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.services.cloud_service import query_from_dataset

logger = logging.getLogger(__name__)


class CloudDatasetParser(BaseDataParser):
    """data parser for database"""
    def __init__(self, dataset_id: str, _: bool, field_specs: Dict[str, FieldSpec]):
        self.dataset_id = dataset_id
        self.example_pandas_df = self._get_example_pandas_df()
        self.field_specs = field_specs

    def _get_example_pandas_df(self) -> pd.DataFrame:
        datas = self._get_all_datas(1000)
        example_df = pd.DataFrame(datas)
        for column in example_df.columns:
            if any(isinstance(val, Decimal) for val in example_df[column]):
                example_df[column] = example_df[column].astype(float)
        return example_df

    @property
    @lru_cache()
    def field_metas(self) -> List[Dict[str, str]]:
        data = self._get_all_datas(1)
        return get_data_meta_type(data[0]) if data else []

    @property
    @lru_cache()
    def raw_fields(self) -> List[Dict[str, str]]:
        pandas_parser = PandasDataFrameDataParser(self.example_pandas_df, False, self.field_specs)
        return [
            {**field, "fid": field["name"]}
            for field in pandas_parser.raw_fields
        ]

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None:
            df = self.example_pandas_df
        else:
            df = self.example_pandas_df[:limit]
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    def get_datas_by_payload(self, payload: Dict[str, Any], _: Optional[int] = None) -> List[Dict[str, Any]]:
        result = query_from_dataset(self.dataset_id, payload)
        return result

    def get_datas_by_sql(self, sql: str, timezone_offset_seconds: Optional[int] = None) -> List[Dict[str, Any]]:
        pass

    def to_csv(self) -> io.BytesIO:
        content = io.BytesIO()
        self.example_pandas_df.toPandas().to_csv(content, index=False)
        return content

    def to_parquet(self) -> io.BytesIO:
        content = io.BytesIO()
        self.example_pandas_df.toPandas().to_parquet(content, index=False, compression="snappy")
        return content

    def _get_all_datas(self, limit: int) -> List[Dict[str, Any]]:
        payload = {"workflow": [{"type": "view", "query": [{"op": "raw", "fields": ["*"]}]}], "limit": limit, "offset": 0}
        return self.get_datas_by_payload(payload)

    @property
    def dataset_tpye(self) -> str:
        return "cloud_dataset"
