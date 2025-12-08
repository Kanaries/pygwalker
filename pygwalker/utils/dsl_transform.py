from typing import Dict, List, Any
import os
import json

try:
    import dukpy
except ImportError as exc:
    raise ImportError("`dukpy` is not installed, please install it first. refer it: `pip install dukpy`.") from exc

from pygwalker._constants import ROOT_DIR
from .randoms import rand_str


class _JSFunction:
    """A wrapper to provide quickjs.Function-like API using dukpy.

    This class loads JavaScript code and allows calling a named function
    from that code with arguments.
    """
    def __init__(self, func_name: str, js_code: str):
        self.func_name = func_name
        self.interpreter = dukpy.JSInterpreter()
        self.interpreter.evaljs(js_code)

    def __call__(self, *args):
        if len(args) == 0:
            return self.interpreter.evaljs(f"{self.func_name}()")
        elif len(args) == 1:
            return self.interpreter.evaljs(f"{self.func_name}(dukpy.arg)", arg=args[0])
        else:
            return self.interpreter.evaljs(f"{self.func_name}.apply(null, dukpy.args)", args=list(args))


with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'dsl-to-workflow.umd.js'), 'r', encoding='utf8') as f:
    _dsl_to_workflow_js = _JSFunction('main', f.read())

with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'vega-to-dsl.umd.js'), 'r', encoding='utf8') as f:
    _vega_to_dsl_js = _JSFunction('main', f.read())


def dsl_to_workflow(dsl: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(_dsl_to_workflow_js(json.dumps(dsl)))


def vega_to_dsl(vega_config: Dict[str, Any], fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    return json.loads(_vega_to_dsl_js(json.dumps({
        "vl": vega_config,
        "allFields": fields,
        "visId": rand_str(6),
        "name": rand_str(6)
    })))
