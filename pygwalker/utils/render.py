import os
import json
from typing import Dict

from jinja2 import Environment, PackageLoader

from pygwalker._constants import BYTE_LIMIT, ROOT_DIR
from pygwalker.utils.randoms import rand_str
from pygwalker import __version__, __hash__
from pygwalker_utils.config import get_config


jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)


def gwalker_script() -> str:
    with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'pygwalker-app.iife.js'), 'r', encoding='utf8') as f:
        gwalker_js = f.read()
    return gwalker_js


class DataFrameEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return str(o)
        except TypeError:
            pass
        return json.JSONEncoder.default(self, o)


def render_gwalker_html(gid: int, props: Dict):
    ds = props.get('dataSource', [])

    props['len'] = len(ds)
    # check too large data
    if len(ds) > 1024:
        smp0 = ds[::len(ds)//32]
        smp1 = ds[::len(ds)//37]
        avg_size = len(json.dumps(smp0, cls=DataFrameEncoder)) / len(smp0)
        avg_size = max(avg_size, len(json.dumps(smp1, cls=DataFrameEncoder)) / len(smp1))
        n = int(BYTE_LIMIT / avg_size)
        if len(ds) >= 2 * n:
            # print(f"PyGWalker doesn't support dataframes that are too large. Using the first {n} rows.")
            props['dataSource'] = ds[:n]

    walker_template = jinja_env.get_template("walk.js")
    props['version'] = __version__
    props['hashcode'] = __hash__
    if 'spec' in props:
        props['visSpec'] = props.get('spec', None)
        del props['spec']
    props['userConfig'], _ = get_config()

    # del props['dataSource']
    props['dataSourceProps'] = {
        'tunnelId': 'tunnel!',
        'dataSourceId': f'dataSource!{rand_str(4)}',
    }

    js = walker_template.render(gwalker={'id': gid, 'props': json.dumps(props, cls=DataFrameEncoder)} )
    js = "var exports={}, module={};" + gwalker_script() + js

    template = jinja_env.get_template("index.html")
    html = f"{template.render(gwalker={'id': gid, 'script': js})}"
    return html
