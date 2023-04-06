from .. import base
from ..base import *
from ..utils.config import get_config
import datetime

def gwalker_script():
    global gwalker_js
    if gwalker_js is None:
        with open(os.path.join(HERE, 'templates', 'dist', 'pygwalker-app.iife.js'), 'r', encoding='utf8') as f:
            gwalker_js = f.read()
    return gwalker_js

from jinja2 import Environment, PackageLoader, select_autoescape
jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()), # select_autoescape()
)

class DataFrameEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime,datetime.date,datetime.time)):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def render_gwalker_html(gid: int, props: tp.Dict):
    ds = props.get('dataSource', [])
    # check too large data
    if len(ds) > 1024:
        smp0 = ds[::len(ds)//32]
        smp1 = ds[::len(ds)//37]
        avg_size = len(json.dumps(smp0, cls=DataFrameEncoder)) / len(smp0)
        avg_size = max(avg_size, len(json.dumps(smp1, cls=DataFrameEncoder)) / len(smp1))
        n = int(BYTE_LIMIT / avg_size)
        if len(ds) >= 2 * n:
            print(f"PyGWalker doesn't support dataframes that are too large. Using the first {n} rows.")
            props['dataSource'] = ds[:n]
    
    walker_template = jinja_env.get_template("walk.js")
    props['version'] = base.__version__
    props['hashcode'] = base.__hash__
    if 'spec' in props:
        props['visSpec'] = props.get('spec', None)
        del props['spec']
    props['userConfig'], _ = get_config()
    
    js = walker_template.render(gwalker={'id': gid, 'props': json.dumps(props, cls=DataFrameEncoder)} )
    js = "var exports={};" + gwalker_script() + js
    
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
