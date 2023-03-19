from ..base import *
from .fname_encodings import fname_decode, fname_encode

class PandasDataFramePropGetter:
    @classmethod
    def infer_prop(cls,s: "pl.Series", i=None) -> tp.Dict:
        """get IMutField

        Args:
            - s (pd.Series): the column
            - i (int, optional): column id. Defaults to None.

        Returns:
            tp.Dict: _description_
        """
        kind = s.dtype.kind
        # print(f'{s.name}: type={s.dtype}, kind={s.dtype.kind}')
        v_cnt = len(s.value_counts())
        semanticType = 'quantitative' if \
            (kind in 'fcmiu' and v_cnt > 16) \
                else 'temporal' if kind in 'M' \
                    else 'nominal' if kind in 'bOSUV' or v_cnt <= 2 \
                        else 'ordinal'
        # 'quantitative' | 'nominal' | 'ordinal' | 'temporal';
        analyticType = 'measure' if \
            kind in 'fcm' or (kind in 'iu' and len(s.value_counts()) > 16) \
                else 'dimension'
        import json
        fname = fname_decode(s.name)
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return {
            'fid': s.name, # f'col-{i}-{s.name}' if i is not None else s.name,
            'name': fname,
            'semanticType': semanticType,
            'analyticType': analyticType
        }
    @classmethod
    def to_records(cls,df: "pd.DataFrame"):
        df = df.replace({float('nan'): None})
        return df.to_dict(orient='records')

    @classmethod
    def raw_fields(cls,df: "pd.DataFrame"):
        return [
            cls.infer_prop(df[col], i)
            for i, col in enumerate(df.columns)
        ]
        
    @classmethod
    def get_props(cls,df: "pd.DataFrame", **kwargs):
        if len(df)*2 > BYTE_LIMIT:
            df = df.iloc[:BYTE_LIMIT//2]
        df = df.reset_index()
        df = df.rename(fname_encode, axis='columns')
        props = {
            'dataSource': cls.to_records(df),
            'rawFields': cls.raw_fields(df),
            'hideDataSourceConfig': kwargs.get('hideDataSourceConfig', True),
            'fieldkeyGuard': False,
            'themeKey': 'g2',
            **kwargs,
        }
        return props

class PolarsDataFramePropGetter:
    @classmethod
    def infer_prop(cls,s: "pl.Series", i=None) -> tp.Dict:
        """get IMutField

        Args:
            - s (pl.Series): the column
            - i (int, optional): column id. Defaults to None.

        Returns:
            tp.Dict: _description_
        """
        kind = s.dtype
        # print(f'{s.name}: type={s.dtype}, kind={s.dtype.kind}')
        v_cnt = len(s.value_counts())
        semanticType = 'quantitative' if \
            (kind in [pl.Int16,pl.Int32,pl.Int64,
                             pl.UInt8,pl.UInt16,pl.UInt32,
                             pl.UInt64,pl.Duration,pl.Float32,pl.Float64] and v_cnt > 16) \
                else 'temporal' if kind in [pl.Datetime,pl.Date,pl.Time] \
                    else 'nominal' if kind in [pl.Boolean,pl.Object,pl.Utf8,pl.Categorical,pl.Struct,pl.List] or v_cnt <= 2 \
                        else 'ordinal'
        # 'quantitative' | 'nominal' | 'ordinal' | 'temporal';
        analyticType = 'measure' if \
            kind in [pl.Float32,pl.Float64,pl.Duration] or (kind in [pl.Int16,pl.Int32,pl.Int64,
                             pl.UInt8,pl.UInt16,pl.UInt32,
                             pl.UInt64] and v_cnt > 16) \
                else 'dimension'
        import json
        fname = fname_decode(s.name)
        fname = json.dumps(fname, ensure_ascii=False)[1:-1]
        return {
            'fid': s.name, # f'col-{i}-{s.name}' if i is not None else s.name,
            'name': fname,
            'semanticType': semanticType,
            'analyticType': analyticType
        }

    @classmethod
    def to_records(cls,df: "pl.DataFrame"):
        df = df.fill_nan(None)
        return df.to_dicts()
    # old style 
    @classmethod
    def raw_fields(cls,df: "pl.DataFrame"):
        return [
            cls.infer_prop(df[col], i)
            for i, col in enumerate(df.columns)
        ]
    #new style using parallel
    @classmethod
    def raw_fields(cls,df: "pl.DataFrame"):
        def colname2fname(s):
            import json
            fname = fname_decode(s)
            fname = json.dumps(fname, ensure_ascii=False)[1:-1]
            return fname
        def colname2semanticType(kind,v_cnt):
            semanticType = 'quantitative' if \
                (kind in ["Int16","Int32","Int64",
                                 "UInt8","UInt16","UInt32",
                                 "UInt64","Duration","Float32","Float64"] and v_cnt > 16) \
                    else 'temporal' if kind in ["Datetime","Date","Time"] \
                        else 'nominal' if kind in ["Boolean","Object","Utf8","Categorical","Struct","List"] or v_cnt <= 2 \
                            else 'ordinal'
            return semanticType
        def colname2analyticType(kind,v_cnt):
            analyticType = 'measure' if \
                kind in ["Float32","Float64","Duration"] or (kind in ["Int16","Int32","Int64",
                                 "UInt8","UInt16","UInt32",
                                 "UInt64"] and v_cnt > 16) \
                else 'dimension'
            return analyticType
        def type2str(t):
            for root_type in (pl.Int16,pl.Int32,pl.Int64,
                             pl.UInt8,pl.UInt16,pl.UInt32,
                             pl.UInt64,pl.Float32,pl.Float64,
                             pl.Datetime,pl.Boolean,pl.Object,pl.Utf8,pl.Date,
                             pl.Categorical,pl.Struct,pl.List,pl.Duration):
                if t == root_type:
                    return str(root_type)
            return str(t)
        counts_data = df.select([pl.col("*").value_counts().count()]).row(0)

        col_info = pl.DataFrame({"fid":df.schema.keys(),
                                # directly storing type instance and appling a function will lead to segmentfault
                                 "kind":map(type2str,df.schema.values()), 
                                 "v_cnt":counts_data},)
        result_data = col_info.select([
            pl.col("fid"),
            pl.col("fid").apply(colname2fname).alias("name"),
            pl.struct(["kind","v_cnt"]).apply(lambda d:colname2semanticType(**d)).alias("semanticType"),
            pl.struct(["kind","v_cnt"]).apply(lambda d:colname2analyticType(**d)).alias("analyticType")
        ])
        return result_data.to_dicts()

    @classmethod
    def get_props(cls,df: "pl.DataFrame", **kwargs):
        if len(df)*2 > BYTE_LIMIT:
            df = df.slice(0, BYTE_LIMIT//2)
        df = df.rename({i : fname_encode(i) for i in df.columns})
        props = {
            'dataSource': cls.to_records(df),
            'rawFields': cls.raw_fields(df),
            'hideDataSourceConfig': kwargs.get('hideDataSourceConfig', True),
            'fieldkeyGuard': False,
            'themeKey': 'g2',
            **kwargs,
        }
        return props

class OtherPropGetter:
    @classmethod
    def get_props(cls,df: "Any", **kwargs):
        return {}

__classname2method = {}
def get_props(df: "pl.DataFrame | pd.DataFrame" , **kwargs):
    df_type = type(df)
    props = __classname2method.get(df_type,OtherPropGetter).get_props(df,**kwargs)
    return props


for module_name in ("pandas","polars"):
    try:
        __import__(module_name)
        if module_name == "polars":
            import polars as pl
            __classname2method[pl.DataFrame] = PolarsDataFramePropGetter
        elif module_name == "pandas":
            import pandas as pd
            __classname2method[pd.DataFrame] = PandasDataFramePropGetter
    except ImportError:
        continue
