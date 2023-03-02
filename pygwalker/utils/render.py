from ..base import *
import datetime

def gwalker_script():
    global gwalker_js
    if gwalker_js is None:
        with open(os.path.join(HERE, 'templates', 'graphic-walker.iife.js'), 'r', encoding='utf8') as f:
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
