from typing import NamedTuple, Generic, Dict, List, Any, Optional
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


class DataFramePropParser(Generic[DataFrame], abc.ABC):
    """DataFrame property getter"""

    @classmethod
    def _infer_semantic(cls, s: Series):
        raise NotImplementedError

    @classmethod
    def _infer_analytic(cls, s: Series):
        raise NotImplementedError

    @classmethod
    def _to_matrix(cls, df: DataFrame) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @classmethod
    def _series(cls, df: DataFrame, i: int, col: str) -> Series:
        return df[col]

    @classmethod
    def _infer_prop(
        cls, df: DataFrame, col: str, i=None, field_specs: Optional[Dict[str, FieldSpec]] = None
    ) -> Dict[str, str]:
        """get IMutField

        Returns:
            (IMutField, Dict)
        """
        if field_specs is None:
            field_specs = {}

        s: cls.Series = cls._series(df, i, col)
        orig_fname = cls._decode_fname(s)
        field_spec = field_specs.get(orig_fname, default_field_spec)
        semantic_type = cls._infer_semantic(s) if field_spec.semanticType == '?' else field_spec.semanticType
        # 'quantitative' | 'nominal' | 'ordinal' | 'temporal';
        analytic_type = cls._infer_analytic(s) if field_spec.analyticType == '?' else field_spec.analyticType
        # 'measure' | 'dimension';
        fname = orig_fname if field_spec.display_as is None else field_spec.display_as
        return {
            'fid': col,
            'name': fname,
            'semanticType': semantic_type,
            'analyticType': analytic_type,
        }

    @classmethod
    def format_data(cls, df: DataFrame) -> DataFrame:
        """Format data"""
        df = df.sample(frac=1)
        df = cls.escape_fname(df)
        return df

    @classmethod
    def escape_fname(cls, df: DataFrame) -> DataFrame:
        """Encode fname to prefent special characters in field name to cause errors"""
        raise NotImplementedError

    @classmethod
    def raw_fields(cls, df: DataFrame, **kwargs):
        field_specs = kwargs.get('fieldSpecs', {})
        return [
            cls._infer_prop(df, col, i, field_specs)
            for i, col in enumerate(df.columns)
        ]

    @classmethod
    def to_records(cls, df: DataFrame, **kwargs) -> List[Dict[str, Any]]:
        """Convert DataFrame to a list of records"""
        raise NotImplementedError
