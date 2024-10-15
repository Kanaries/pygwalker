from typing import Generic, Dict, List, Any, Optional
from typing_extensions import Literal
from functools import lru_cache
from datetime import datetime, date
from datetime import timedelta
import abc
import io

from pydantic import BaseModel
import duckdb
import arrow
import pytz

from pygwalker._typing import DataFrame
from pygwalker.utils.payload_to_sql import get_sql_from_payload
from pygwalker.utils.estimate_tools import estimate_average_data_size


# pylint: disable=broad-except
class FieldSpec(BaseModel):
    """Field specification.

    Args:
    - fname: str. The field name.
    - semantic_type: '?' | 'nominal' | 'ordinal' | 'temporal' | 'quantitative'. default to '?'.
    - analytic_type: '?' | 'dimension' | 'measure'. default to '?'.
    - display_as: str. The field name displayed. None means using the original column name.
    """
    fname: str
    semantic_type: Literal['?', 'nominal', 'ordinal', 'temporal', 'quantitative'] = '?'
    analytic_type: Literal['?', 'dimension', 'measure'] = '?'
    display_as: str = None


INFINITY_DATA_SIZE = 1 << 62


class BaseDataParser(abc.ABC):
    """Base class for data parser"""

    @abc.abstractmethod
    def __init__(
        self,
        data: Any,
        field_specs: List[FieldSpec],
        infer_string_to_date: bool,
        infer_number_to_dimension: bool,
        other_params: Dict[str, Any]
    ) -> None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def raw_fields(self) -> List[Dict[str, str]]:
        """get raw fields"""
        raise NotImplementedError

    @abc.abstractmethod
    def to_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        """get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def batch_get_datas_by_sql(self, sql_list: List[str]) -> List[List[Dict[str, Any]]]:
        """batch get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def batch_get_datas_by_payload(self, payload_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """batch get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def to_csv(self) -> io.BytesIO:
        """get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def to_parquet(self) -> io.BytesIO:
        """get records"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def dataset_type(self) -> str:
        """get dataset type"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def field_metas(self) -> List[Dict[str, str]]:
        """get field metas"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def placeholder_table_name(self) -> str:
        """get placeholder table name"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def data_size(self) -> int:
        """Estimate data bytes size"""
        raise NotImplementedError


class BaseDataFrameDataParser(Generic[DataFrame], BaseDataParser):
    """DataFrame property getter"""
    def __init__(
        self, df: DataFrame,
        field_specs: List[FieldSpec],
        infer_string_to_date: bool,
        infer_number_to_dimension: bool,
        other_params: Dict[str, Any]
    ):
        self.origin_df = df
        self.df = self._rename_dataframe(df)
        self._example_df = self.df[:1000]
        self.field_specs = field_specs
        self._duckdb_df = self.df
        self.infer_string_to_date = infer_string_to_date
        self.infer_number_to_dimension = infer_number_to_dimension
        self.other_params = other_params

    @property
    @lru_cache()
    def field_metas(self) -> List[Dict[str, str]]:
        duckdb.register("pygwalker_mid_table", self._duckdb_df)
        result = duckdb.query("SELECT * FROM pygwalker_mid_table LIMIT 1")
        data = result.fetchone()
        return get_data_meta_type(dict(zip(result.columns, data))) if data else []

    @property
    @lru_cache()
    def raw_fields(self) -> List[Dict[str, str]]:
        return [
            self._infer_prop(col, self.field_specs)
            for _, col in enumerate(self._example_df.columns)
        ]

    def _infer_prop(
        self, col: str, field_specs: List[FieldSpec] = None
    ) -> Dict[str, str]:
        """get IMutField

        Returns:
            (IMutField, Dict)
        """
        s = self._example_df[col]
        orig_fname = col

        field_spec_map = {field_spec.fname: field_spec for field_spec in field_specs}

        field_spec = field_spec_map.get(orig_fname, FieldSpec(fname=orig_fname))
        semantic_type = self._infer_semantic(s, orig_fname) if field_spec.semantic_type == '?' else field_spec.semantic_type
        analytic_type = self._infer_analytic(s, orig_fname) if field_spec.analytic_type == '?' else field_spec.analytic_type
        fname = orig_fname if field_spec.display_as is None else field_spec.display_as
        return {
            'fid': col,
            'name': fname,
            'semanticType': semantic_type,
            'analyticType': analytic_type,
        }

    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        """get datas by duckdb"""
        try:
            duckdb.query("SET TimeZone = 'UTC'")
        except Exception:
            pass

        duckdb.register("pygwalker_mid_table", self._duckdb_df)

        result = duckdb.query(sql)
        return [
            dict(zip(result.columns, row))
            for row in result.fetchall()
        ]

    def _rename_dataframe(self, df: DataFrame) -> DataFrame:
        """rename dataframe"""
        raise NotImplementedError

    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        sql = get_sql_from_payload(
            "pygwalker_mid_table",
            payload,
            {"pygwalker_mid_table": self.field_metas}
        )
        return self.get_datas_by_sql(sql)

    def batch_get_datas_by_sql(self, sql_list: List[str]) -> List[List[Dict[str, Any]]]:
        """batch get records"""
        return [
            self.get_datas_by_sql(sql)
            for sql in sql_list
        ]

    def batch_get_datas_by_payload(self, payload_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """batch get records"""
        return [
            self.get_datas_by_payload(payload)
            for payload in payload_list
        ]

    @property
    def dataset_type(self) -> str:
        return "dataframe_default"

    @property
    def placeholder_table_name(self) -> str:
        return "pygwalker_mid_table"

    @property
    def data_size(self) -> int:
        datas = self.to_records(300)
        avg_size = estimate_average_data_size(datas)
        return avg_size * self.df.shape[0]


def is_temporal_field(value: Any, infer_string_to_date: bool) -> bool:
    """check if field is temporal"""
    if infer_string_to_date:
        try:
            arrow.get(str(value))
        except Exception:
            return False
        return True

    return isinstance(value, (datetime, date))


def is_geo_field(field_name: str) -> bool:
    """check if filed is """
    field_name = field_name.lower().strip(" .")
    return field_name in {
        "latitude", "longitude",
        "lat", "long", "lon"
    }


def format_temporal_string(value: str) -> str:
    """Convert temporal fields to a fixed format"""
    return arrow.get(value).strftime("%Y-%m-%d %H:%M:%S")


def get_data_meta_type(data: Dict[str, Any]) -> List[Dict[str, str]]:
    meta_types = []
    for key, value in data.items():
        if isinstance(value, datetime):
            field_meta_type = "datetime"
            if value.tzinfo:
                field_meta_type = "datetime_tz"
        elif isinstance(value, (int, float)):
            field_meta_type = "number"
        else:
            field_meta_type = "string"
        meta_types.append({
            "key": key,
            "type": field_meta_type
        })
    return meta_types


@lru_cache()
def get_timezone_base_offset(offset_seconds: int) -> Optional[str]:
    utc_offset = timedelta(seconds=offset_seconds)
    now = datetime.now(pytz.utc)
    for tz in map(pytz.timezone, pytz.all_timezones_set):
        if now.astimezone(tz).utcoffset() == utc_offset:
            return tz.zone
