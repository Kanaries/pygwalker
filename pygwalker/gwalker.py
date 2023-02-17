from .base import *

global_gid = 0

def to_records(df: pd.DataFrame):
    
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
    autoescape=select_autoescape()
)

def render_gwalker_html(gid: int):
    template = jinja_env.get_template("index.html")
    html = f"{template.render(gwalker={'id': gid})}"
    return html

class DataFrameEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def render_gwalker_js(gid: int, props: tp.Dict):
    walker_template = jinja_env.get_template("walk.js")
    js = walker_template.render(gwalker={'id': gid, 'props': json.dumps(props, cls=DataFrameEncoder)} )
    return gwalker_script() + js
    
def walk(df: pd.DataFrame, gid: tp.Union[int, str]=None, **kwargs):
    """walk through pandas.DataFrame df with Graphic Walker

    Args:
        df (pd.DataFrame, optional): dataframe.
        gid (tp.Union[int, str], optional): GraphicWalker container div's id ('gwalker-{gid}')
    """
    global global_gid
    gid = kwargs.get('gid', None)
    if gid is None:
        gid = global_gid
        global_gid += 1
    props = {
        'dataSource': to_records(df),
        'rawFields': raw_fields(df),
    }
    html = render_gwalker_html(gid)
    js = render_gwalker_js(gid, props)
    
    display(HTML(html))
    display(Javascript(js))
    # html = f"{html}<body><script>{js}</script></body>"
    # html = html.replace("\"", "\\\"")
    # print(html)
    # display(IFrame(src="", width="500px", height="500px", extras=[f"srcdoc=\"{html}\""]))

class GWalker:
    def __init__(self, df: pd.DataFrame=None, **kwargs):
        global global_gid
        self.gid = global_gid
        global_gid += 1
        self.df = df
    
    def walk(self, **kwargs):
        props = {
            'dataSource': self.dataSource,
            'rawFields': self.rawFields,
        }
        html = render_gwalker_html(self.gid)
        js = render_gwalker_js(self.gid, props)
        
        display(HTML(html))
        display(Javascript(js))
        
    def update(self, df: pd.DataFrame=None, **kwargs):
        pass
    
    @property
    def dataSource(self) -> tp.List[tp.Dict]:
        return to_records(self.df)
    
    @property
    def rawFields(self) -> tp.List:
        return raw_fields(self.df)
    