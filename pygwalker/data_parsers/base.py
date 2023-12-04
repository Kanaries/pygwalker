from typing import NamedTuple, Generic, Dict, List, Any, Optional
from typing_extensions import Literal
from functools import lru_cache
from datetime import datetime
from datetime import timedelta
import abc
import io

from sqlglot import column as column_func
import duckdb
import arrow
import pytz

from pygwalker._typing import DataFrame
from pygwalker.utils.payload_to_sql import get_sql_from_payload


# pylint: disable=broad-except
class FieldSpec(NamedTuple):
    """Field specification.

    Args:
    - semanticType: '?' | 'nominal' | 'ordinal' | 'temporal' | 'quantitative'. default to '?'.
    - analyticType: '?' | 'dimension' | 'measure'. default to '?'.
    - display_as: str. The field name displayed. None means using the original column name.
    """
    semanticType: Literal['?', 'nominal', 'ordinal', 'temporal', 'quantitative'] = '?'
    analyticType: Literal['?', 'dimension', 'measure'] = '?'
    display_as: str = None


default_field_spec = FieldSpec()


class BaseDataParser(abc.ABC):
    """Base class for data parser"""

    @abc.abstractmethod
    def __init__(self, data: Any, use_kernel_calc: bool, field_specs: Dict[str, FieldSpec]) -> None:
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
    def get_datas_by_sql(self, sql: str, timezone_offset_seconds: Optional[int] = None) -> List[Dict[str, Any]]:
        """get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_datas_by_payload(self, payload: Dict[str, Any], timezone_offset_seconds: Optional[int] = None) -> List[Dict[str, Any]]:
        """get records"""
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
    def dataset_tpye(self) -> str:
        """get dataset type"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def field_metas(self) -> List[Dict[str, str]]:
        """get field metas"""
        raise NotImplementedError


class BaseDataFrameDataParser(Generic[DataFrame], BaseDataParser):
    """DataFrame property getter"""
    def __init__(self, df: DataFrame, use_kernel_calc: bool, field_specs: Dict[str, FieldSpec]):
        self.origin_df = df
        self.df = self._rename_dataframe(df)
        self._example_df = self.df[:1000]
        self.use_kernel_calc = use_kernel_calc
        self.field_specs = field_specs
        if self.use_kernel_calc:
            self.df = self._preprocess_dataframe(self.df)
        self._duckdb_df = self.df

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
        self, col: str, field_specs: Dict[str, FieldSpec] = None
    ) -> Dict[str, str]:
        """get IMutField

        Returns:
            (IMutField, Dict)
        """
        s = self._example_df[col]
        orig_fname = col
        field_spec = field_specs.get(orig_fname, default_field_spec)
        semantic_type = self._infer_semantic(s, orig_fname) if field_spec.semanticType == '?' else field_spec.semanticType
        analytic_type = self._infer_analytic(s, orig_fname) if field_spec.analyticType == '?' else field_spec.analyticType
        fname = orig_fname if field_spec.display_as is None else field_spec.display_as
        return {
            'fid': col,
            'name': fname,
            'semanticType': semantic_type,
            'analyticType': analytic_type,
        }

    def get_datas_by_sql(self, sql: str, timezone_offset_seconds: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Due to duckdb don't support use 'EPOCH FROM' timestamp_s, timestamp_ms.
        So we need to convert timestamp_s, timestamp_ms to timestamp temporarily.
        """
        if timezone_offset_seconds is not None:
            timezone = get_timezone_base_offset(timezone_offset_seconds)
            if timezone:
                try:
                    duckdb.query(f"SET TimeZone = '{timezone}'")
                except Exception:
                    pass

        duckdb.register("__pygwalker_mid_table", self._duckdb_df)

        select_expr_list = []
        for field in self.field_metas:
            origin_field = str(column_func(field["key"], quoted=True))
            if field["type"] != "datetime":
                select_expr_list.append(origin_field)
            else:
                select_expr_list.append(f'{origin_field}::timestamp {origin_field}')
        select_expr = ",".join(select_expr_list)

        sql = f"""
            WITH pygwalker_mid_table AS (
                SELECT
                    {select_expr}
                FROM
                    "__pygwalker_mid_table"
            )
            {sql}
        """
        result = duckdb.query(sql)
        return [
            dict(zip(result.columns, row))
            for row in result.fetchall()
        ]

    def _rename_dataframe(self, df: DataFrame) -> DataFrame:
        """rename dataframe"""
        raise NotImplementedError

    def _preprocess_dataframe(self, df: DataFrame) -> DataFrame:
        """preprocess dataframe"""
        raise NotImplementedError

    def get_datas_by_payload(self, payload: Dict[str, Any], timezone_offset_seconds: Optional[int] = None) -> List[Dict[str, Any]]:
        sql = get_sql_from_payload(
            "pygwalker_mid_table",
            payload,
            {"pygwalker_mid_table": self.field_metas}
        )
        return self.get_datas_by_sql(sql, timezone_offset_seconds)

    @property
    def dataset_tpye(self) -> str:
        return "dataframe_default"


def is_temporal_field(value: str) -> bool:
    """check if field is temporal"""
    try:
        arrow.get(value)
    except Exception:
        return False
    return True


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
