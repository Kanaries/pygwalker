from typing import Dict, List, Any
import os
import json

try:
    from quickjs import Function
except ImportError as exc:
    raise ImportError("`quickjs` is not installed, please install it first. refer it: `pip install quickjs`.") from exc

from pygwalker._constants import ROOT_DIR
from .randoms import rand_str


with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'dsl-to-workflow.umd.js'), 'r', encoding='utf8') as f:
    _dsl_to_workflow_js = Function('main', f.read())

with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'vega-to-dsl.umd.js'), 'r', encoding='utf8') as f:
    _vega_to_dsl_js = Function('main', f.read())


def dsl_to_workflow(dsl: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(_dsl_to_workflow_js(json.dumps(dsl)))


def vega_to_dsl(vega_config: Dict[str, Any], fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    return json.loads(_vega_to_dsl_js(json.dumps({
        "vl": vega_config,
        "allFields": fields,
        "visId": rand_str(6),
        "name": rand_str(6)
    })))
