from typing import NamedTuple, Generic, Dict, List, Any, Optional
from typing_extensions import Literal
from functools import lru_cache
from datetime import datetime
import abc
import io

import arrow

from pygwalker._typing import DataFrame


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
    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        """get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """get records"""
        raise NotImplementedError

    @abc.abstractmethod
    def to_csv(self) -> io.BytesIO:
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

    @property
    @lru_cache()
    def field_metas(self) -> List[Dict[str, str]]:
        data = self.get_datas_by_sql("SELECT * FROM pygwalker_mid_table LIMIT 1")
        return get_data_meta_type(data[0]) if data else []

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
        orig_fname = self._decode_fname(s)
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

    def _rename_dataframe(self, df: DataFrame) -> DataFrame:
        """rename dataframe"""
        raise NotImplementedError

    def _preprocess_dataframe(self, df: DataFrame) -> DataFrame:
        """preprocess dataframe"""
        raise NotImplementedError

    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    @property
    def dataset_tpye(self) -> str:
        return "dataframe_default"


def is_temporal_field(value: str) -> bool:
    """check if field is temporal"""
    try:
        arrow.get(value)
    except:
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
            data[key] = format_temporal_string(value)
            field_meta_type = "datetime"
        elif isinstance(value, (int, float)):
            field_meta_type = "number"
        else:
            field_meta_type = "string"
        meta_types.append({
            "key": key,
            "type": field_meta_type
        })
    return meta_types
