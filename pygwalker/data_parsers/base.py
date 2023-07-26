from typing import NamedTuple, Generic, Dict, List, Any
from typing_extensions import Literal
import abc

from pygwalker._typing import DataFrame, Series


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
    def __init__(self, data: Any) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def raw_fields(self, field_specs: Dict[str, FieldSpec]) -> List[Dict[str, str]]:
        """get raw fields"""
        raise NotImplementedError

    @abc.abstractmethod
    def to_records(self) -> List[Dict[str, Any]]:
        """get records"""
        raise NotImplementedError


class BaseDataFrameDataParser(Generic[DataFrame], BaseDataParser):
    """DataFrame property getter"""
    def __init__(self, df: DataFrame):
        self.df = self._init_dataframe(df)

    def raw_fields(self, field_specs: Dict[str, FieldSpec]) -> List[Dict[str, str]]:
        return [
            self._infer_prop(col, field_specs)
            for _, col in enumerate(self.df.columns)
        ]

    def to_records(self) -> List[Dict[str, Any]]:
        """Convert DataFrame to a list of records"""
        raise NotImplementedError

    def _init_dataframe(self, df: DataFrame) -> DataFrame:
        raise NotImplementedError

    def _infer_semantic(self, s: Series) -> Literal['quantitative', 'nominal', 'ordinal', 'temporal']:
        raise NotImplementedError

    def _infer_analytic(self, s: Series) -> Literal['measure', 'dimension']:
        raise NotImplementedError

    def _series(self, col: str) -> Series:
        return self.df[col]

    def _infer_prop(
        self, col: str, field_specs: Dict[str, FieldSpec] = None
    ) -> Dict[str, str]:
        """get IMutField

        Returns:
            (IMutField, Dict)
        """
        s = self._series(col)
        orig_fname = self._decode_fname(s)
        field_spec = field_specs.get(orig_fname, default_field_spec)
        semantic_type = self._infer_semantic(s) if field_spec.semanticType == '?' else field_spec.semanticType
        analytic_type = self._infer_analytic(s) if field_spec.analyticType == '?' else field_spec.analyticType
        fname = orig_fname if field_spec.display_as is None else field_spec.display_as
        return {
            'fid': col,
            'name': fname,
            'semanticType': semantic_type,
            'analyticType': analytic_type,
        }
