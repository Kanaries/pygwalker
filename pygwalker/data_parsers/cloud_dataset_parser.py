from typing import Any, Dict, List, Optional
from threading import Lock
from decimal import Decimal
import logging
import io

import pandas as pd

from .base import BaseDataParser, get_data_meta_type, INFINITY_DATA_SIZE
from .pandas_parser import PandasDataFrameDataParser
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.services.cloud_service import CloudService

logger = logging.getLogger(__name__)


class CloudDatasetParser(BaseDataParser):
    """data parser for database"""
    def __init__(
        self,
        dataset_id: str,
        field_specs: List[FieldSpec],
        infer_string_to_date: bool,
        infer_number_to_dimension: bool,
        other_params: Dict[str, Any]
    ):
        self.dataset_id = dataset_id
        self.field_specs = field_specs
        self.infer_string_to_date = infer_string_to_date
        self.infer_number_to_dimension = infer_number_to_dimension
        self.other_params = other_params
        self._cloud_service = CloudService(other_params.get("kanaries_api_key", ""))
        self.example_pandas_df = self._get_example_pandas_df()
        self._field_metas_cache = None
        self._raw_fields_cache = None
        self._cache_lock = Lock()

    def _get_example_pandas_df(self) -> pd.DataFrame:
        datas = self._get_all_datas(1000)
        example_df = pd.DataFrame(datas)
        for column in example_df.columns:
            if any(isinstance(val, Decimal) for val in example_df[column]):
                example_df[column] = example_df[column].astype(float)
        return example_df

    @property
    def field_metas(self) -> List[Dict[str, str]]:
        cache = self._field_metas_cache
        if cache is not None:
            return cache
        with self._cache_lock:
            if self._field_metas_cache is None:
                data = self._get_all_datas(1)
                self._field_metas_cache = get_data_meta_type(data[0]) if data else []
            return self._field_metas_cache

    @property
    def raw_fields(self) -> List[Dict[str, str]]:
        cache = self._raw_fields_cache
        if cache is not None:
            return cache
        with self._cache_lock:
            if self._raw_fields_cache is None:
                pandas_parser = PandasDataFrameDataParser(
                    self.example_pandas_df,
                    self.field_specs,
                    self.infer_string_to_date,
                    self.infer_number_to_dimension,
                    self.other_params
                )
                self._raw_fields_cache = [
                    {**field, "fid": field["name"]}
                    for field in pandas_parser.raw_fields
                ]
            return self._raw_fields_cache

    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None:
            df = self.example_pandas_df
        else:
            df = self.example_pandas_df[:limit]
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = self._cloud_service.query_from_dataset(self.dataset_id, payload)
        return result

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
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

    def batch_get_datas_by_sql(self, sql_list: List[str]) -> List[List[Dict[str, Any]]]:
        """batch get records"""
        pass

    def batch_get_datas_by_payload(self, payload_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """batch get records"""
        result = self._cloud_service.batch_query_from_dataset(self.dataset_id, payload_list)
        return [
            item["rows"]
            for item in result
        ]

    @property
    def dataset_type(self) -> str:
        return "cloud_dataset"

    @property
    def placeholder_table_name(self) -> str:
        return "pygwalker_mid_table"

    @property
    def data_size(self) -> int:
        return INFINITY_DATA_SIZE
