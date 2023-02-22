from .base import *

global_gid = 0

def to_records(df: pd.DataFrame):
    df = df.replace({float('nan'): None})
    return df.to_dict(orient='records')

def raw_fields(df: pd.DataFrame):
    return [
        infer_type(df[col], i)
        for i, col in enumerate(df.columns)
    ]

def infer_type(s: pd.Series, i=None) -> tp.Dict:
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
        'name': s.name,
        'semanticType': semanticType,
        'analyticType': analyticType
    }
    
from jinja2 import Environment, PackageLoader, select_autoescape
jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()), # select_autoescape()
)

class DataFrameEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def render_gwalker_html(gid: int, props: tp.Dict):
    walker_template = jinja_env.get_template("walk.js")
    js = walker_template.render(gwalker={'id': gid, 'props': json.dumps(props, cls=DataFrameEncoder)} )
    js = "var exports={};var process={env:{NODE_ENV:\"production\"} };" + gwalker_script() + js
    
    template = jinja_env.get_template("index.html")
    html = f"{template.render(gwalker={'id': gid, 'script': js})}"
    # print("html =", html)
    return html

def render_gwalker_js(gid: int, props: tp.Dict):
    pass
    # walker_template = jinja_env.get_template("walk.js")
    # js = walker_template.render(gwalker={'id': gid, 'props': json.dumps(props, cls=DataFrameEncoder)} )
    # js = gwalker_script() + js
    # return js

def get_props(df: pd.DataFrame, **kwargs):
    props = {
        'dataSource': to_records(df),
        'rawFields': raw_fields(df),
        'hideDataSourceConfig': kwargs.get('hideDataSourceConfig', True),
    }
    return props

def to_html(df: pd.DataFrame, gid: tp.Union[int, str]=None, **kwargs):
    """Generate embeddable HTML code of Graphic Walker with data of `df`.

    Args:
        df (pd.DataFrame, optional): dataframe.
        gid (tp.Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
        hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
    """
    global global_gid
    gid = kwargs.get('gid', None)
    if gid is None:
        gid = global_gid
        global_gid += 1
    props = get_props(df, **kwargs)
    html = render_gwalker_html(gid, props)
    return html
    
def walk(df: pd.DataFrame, gid: tp.Union[int, str]=None, **kwargs):
    """walk through pandas.DataFrame df with Graphic Walker

    Args:
        df (pd.DataFrame, optional): dataframe.
        gid (tp.Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
        hideDataSourceConfig (bool, optional): Hide DataSource import and export button (True) or not (False). Default to True
    """
    global global_gid
    gid = kwargs.get('gid', None)
    if gid is None:
        gid = global_gid
        global_gid += 1
    html = to_html(df, gid, **kwargs)
    display(HTML(html))

class GWalker:
    def __init__(self, df: pd.DataFrame=None, **kwargs):
        global global_gid
        self.gid = global_gid
        global_gid += 1
        self.df = df
    
    def to_html(self, **kwargs):
        html = to_html(self.df, self.gid, **kwargs)
        return html
    
    def walk(self, **kwargs):
        html = self.to_html(**kwargs)
        display(HTML(html))
        
    def update(self, df: pd.DataFrame=None, **kwargs):
        pass
    
    @property
    def dataSource(self) -> tp.List[tp.Dict]:
        return to_records(self.df)
    
    @property
    def rawFields(self) -> tp.List:
        return raw_fields(self.df)
    