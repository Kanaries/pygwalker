from typing import NamedTuple, TYPE_CHECKING, TypeVar, Generic, Dict, List, Any, Optional
from typing_extensions import Literal
import abc


dataframe_types = []
if TYPE_CHECKING:
    try:
        import pandas as pd
        dataframe_types.append(pd.DataFrame)
    except ModuleNotFoundError:
        pass
    try:
        from modin import pandas as mpd
        dataframe_types.append(mpd.DataFrame)
    except ModuleNotFoundError:
        pass
    try:
        import polars as pl
        dataframe_types.append(pl.DataFrame)
    except ModuleNotFoundError:
        pass


DataFrame = TypeVar("DataFrame", *dataframe_types)
Series = TypeVar("Series")


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
    def infer_semantic(cls, s: Series, **kwargs):
        raise NotImplementedError

    @classmethod
    def infer_analytic(cls, s: Series, **kwargs):
        raise NotImplementedError

    @classmethod
    def to_records(cls, df: DataFrame, **kwargs) -> List[Dict[str, Any]]:
        """Convert DataFrame to a list of records"""
        raise NotImplementedError

    @classmethod
    def to_matrix(cls, df: DataFrame, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @classmethod
    def escape_fname(cls, df: DataFrame, **kwargs) -> DataFrame:
        """Encode fname to prefent special characters in field name to cause errors"""
        raise NotImplementedError

    @classmethod
    def series(cls, df: DataFrame, i: int, col: str) -> Series:
        return df[col]

    @classmethod
    def infer_prop(
        cls, df: DataFrame, col: str, i=None, field_specs: Optional[Dict[str, FieldSpec]] = None
    ) -> Dict[str, str]:
        """get IMutField

        Returns:
            (IMutField, Dict)
        """
        if field_specs is None:
            field_specs = {}

        s: cls.Series = cls.series(df, i, col)
        orig_fname = cls.decode_fname(s)
        field_spec = field_specs.get(orig_fname, default_field_spec)
        semantic_type = cls.infer_semantic(s) if field_spec.semanticType == '?' else field_spec.semanticType
        # 'quantitative' | 'nominal' | 'ordinal' | 'temporal';
        analytic_type = cls.infer_analytic(s) if field_spec.analyticType == '?' else field_spec.analyticType
        # 'measure' | 'dimension';
        fname = orig_fname if field_spec.display_as is None else field_spec.display_as
        return {
            'fid': col,
            'name': fname,
            'semanticType': semantic_type,
            'analyticType': analytic_type,
        }

    @classmethod
    def raw_fields(cls, df: DataFrame, **kwargs):
        field_specs = kwargs.get('fieldSpecs', {})
        return [
            cls.infer_prop(df, col, i, field_specs)
            for i, col in enumerate(df.columns)
        ]

    @classmethod
    def limited_sample(cls, df: DataFrame) -> DataFrame:
        """Return the max sample that can be sent to GraphicWalker"""
        raise NotImplementedError

    @classmethod
    def get_props(cls, df: DataFrame, **kwargs):
        """Remove data volume restrictions for non-JUPyter environments.

        Kargs:
            - env: (Literal['Jupyter' | 'Streamlit'], optional): The enviroment using pygwalker from program entry. Default as 'Jupyter'
        """
        if kwargs.get('env') == 'Jupyter':
            df = cls.limited_sample(df)
        df = cls.escape_fname(df, **kwargs)
        props = {
            'dataSource': cls.to_records(df),
            'rawFields': cls.raw_fields(df, **kwargs),
            'hideDataSourceConfig': kwargs.get('hideDataSourceConfig', True),
            'fieldkeyGuard': False,
            'themeKey': 'g2',
            **kwargs,
        }
        return props

    @classmethod
    def decode_fname(cls, s: Series, **kwargs) -> str:
        """Get safe field name from series."""
        raise NotImplementedError
