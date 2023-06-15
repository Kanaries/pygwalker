from typing import NamedTuple, TYPE_CHECKING, TypeVar, Generic, Dict, List, Any, Optional
from typing_extensions import Literal
from types import ModuleType
import sys
import json

from .fname_encodings import fname_decode, fname_encode
from pygwalker.base import BYTE_LIMIT


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

dataframe_types = []
if TYPE_CHECKING:
    try:
        import pandas as pd
        dataframe_types.append(pd.DataFrame)
    except ModuleNotFoundError:
        pass
    try:
        import polars as pl
        dataframe_types.append(pl.DataFrame)
    except ModuleNotFoundError:
        pass


DataFrame = TypeVar("DataFrame", *dataframe_types)
"""
DataFrame can be either pandas.DataFrame or polars.DataFrame
"""


class DataFramePropGetter(Generic[DataFrame]):
    """DataFrame property getter"""
    Series = TypeVar("Series")

    @classmethod
    def infer_semantic(cls, df: DataFrame, **kwargs):
        raise NotImplementedError

    @classmethod
    def infer_analytic(cls, df: DataFrame, **kwargs):
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


class PandasDataFramePropGetter(DataFramePropGetter[DataFrame]):
    pass


class PolarsDataFramePropGetter(DataFramePropGetter[DataFrame]):
    pass


__classname2method = {}
__supported_modules = ['pandas', 'polars']


def _build_pandas_prop_getter(pd: ModuleType):

    class PandasDataFramePropGetter(DataFramePropGetter[pd.DataFrame]):
        @classmethod
        def limited_sample(cls, df: DataFrame) -> DataFrame:
            if len(df)*2 > BYTE_LIMIT:
                df = df.iloc[:BYTE_LIMIT//2]
            return df

        @classmethod
        def infer_semantic(cls, s: pd.Series):
            v_cnt = len(s.value_counts())
            kind = s.dtype.kind
            return 'quantitative' if (kind in 'fcmiu' and v_cnt > 16) else \
                'temporal' if kind in 'M' else \
                'nominal' if kind in 'bOSUV' or v_cnt <= 2 else \
                'ordinal'

        @classmethod
        def infer_analytic(cls, s: pd.Series):
            kind = s.dtype.kind
            return 'measure' if \
                kind in 'fcm' or (kind in 'iu' and len(s.value_counts()) > 16) \
                    else 'dimension'

        @classmethod
        def series(cls, df: pd.DataFrame, i: int, col: str):
            return df.iloc[:, i]

        @classmethod
        def to_records(cls, df: pd.DataFrame):
            df = df.replace({float('nan'): None})
            return df.to_dict(orient='records')

        @classmethod
        def to_matrix(cls, df: pd.DataFrame, **kwargs) -> List[List[Any]]:
            df = df.replace({float('nan'): None})
            return df.to_dict(orient='tight')

        @classmethod
        def escape_fname(cls, df: pd.DataFrame, **kwargs):
            df = df.reset_index()
            df.columns = [f"{col}_{i}" for i, col in enumerate(df.columns)]
            df = df.rename(fname_encode, axis='columns')
            return df

        @classmethod
        def decode_fname(cls, s: pd.Series, **kwargs):
            fname = fname_decode(s.name)
            fname = json.dumps(fname, ensure_ascii=False)[1:-1]
            return fname

    return PandasDataFramePropGetter


def _build_polars_prop_getter(pl: ModuleType):
    class PolarsDataFramePropGetter(DataFramePropGetter[pl.DataFrame]):
        Series = pl.Series
        @classmethod
        def limited_sample(cls, df: DataFrame) -> DataFrame:
            if len(df)*2 > BYTE_LIMIT:
                df = df.head(BYTE_LIMIT//2)
            return df

        @classmethod
        def infer_semantic(cls, s: pl.Series):
            v_cnt = len(s.value_counts())
            kind = s.dtype
            return 'quantitative' if kind in pl.NUMERIC_DTYPES and v_cnt > 16 else \
                'temporal' if kind in pl.TEMPORAL_DTYPES else \
                'nominal' if kind in [pl.Boolean, pl.Object, pl.Utf8, pl.Categorical, pl.Struct, pl.List] or v_cnt <= 2 else \
                'ordinal'

        @classmethod
        def infer_analytic(cls, s: pl.Series):
            kind = s.dtype
            return 'measure' if kind in pl.FLOAT_DTYPES | pl.DURATION_DTYPES or \
                   (kind in pl.INTEGER_DTYPES and len(s.value_counts()) > 16) else \
                'dimension'

        @classmethod
        def to_records(cls, df: pl.DataFrame, **kwargs) -> List[Dict[str, Any]]:
            df = df.fill_nan(None)
            return df.to_dicts()

        @classmethod
        def to_matrix(cls, df: pl.DataFrame, **kwargs) -> List[Dict[str, Any]]:
            df = df.fill_nan(None)
            dicts = df.to_dicts()
            return {'columns': list(dicts[0].keys()), 'data': [list(d.values()) for d in dicts]}

        @classmethod
        def escape_fname(cls, df: pl.DataFrame, **kwargs) -> pl.DataFrame:
            df = df.rename({i: fname_encode(i) for i in df.columns})
            return df

        @classmethod
        def decode_fname(cls, s: pl.Series, **kwargs):
            fname = fname_decode(s.name)
            fname = json.dumps(fname, ensure_ascii=False)[1:-1]
            return fname

    return PolarsDataFramePropGetter


def get_prop_getter(df: DataFrame) -> DataFramePropGetter:
    if type(df) in __classname2method:
        return __classname2method[type(df)]

    if 'pandas' in sys.modules:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            __classname2method[pd.DataFrame] = _build_pandas_prop_getter(pd)
            return __classname2method[pd.DataFrame]

    if 'polars' in sys.modules:   
        import polars as pl
        if isinstance(df, pl.DataFrame):
            __classname2method[pl.DataFrame] = _build_polars_prop_getter(pl)
            return __classname2method[pl.DataFrame]
    return DataFramePropGetter


def get_props(df: DataFrame, **kwargs):
    props = get_prop_getter(df).get_props(df, **kwargs)
    return props
