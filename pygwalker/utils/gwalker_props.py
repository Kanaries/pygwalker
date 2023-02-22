from ..base import *
from .fname_encodings import fname_decode, fname_encode

def infer_prop(s: pd.Series, i=None) -> tp.Dict:
    """get IMutField

    Args:
        s (pd.Series): the column
        i (int, optional): column id. Defaults to None.

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
    return {
        'fid': s.name, # f'col-{i}-{s.name}' if i is not None else s.name,
        'name': fname_decode(s.name),
        'semanticType': semanticType,
        'analyticType': analyticType
    }
    
def to_records(df: pd.DataFrame):
    df = df.replace({float('nan'): None})
    return df.to_dict(orient='records')

def raw_fields(df: pd.DataFrame):
    return [
        infer_prop(df[col], i)
        for i, col in enumerate(df.columns)
    ]

def get_props(df: pd.DataFrame, **kwargs):
    df = df.rename(fname_encode, axis='columns')
    props = {
        'dataSource': to_records(df),
        'rawFields': raw_fields(df),
        'hideDataSourceConfig': kwargs.get('hideDataSourceConfig', True),
    }
    return props