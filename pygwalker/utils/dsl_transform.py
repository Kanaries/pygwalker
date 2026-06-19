from typing import Dict, List, Any
import os
import json

from pygwalker._constants import ROOT_DIR
from .randoms import rand_str

_dsl_to_workflow_js = None  # type: Optional[Callable]
_vega_to_dsl_js = None  # type: Optional[Callable]

_INSTALL_MSG = (
    "Static HTML chart export requires a JavaScript runtime.\n"
    "Install with: pip install pygwalker[export]\n"
    "Or manually: pip install mini-racer"
)


def _make_js_callable(func_name, js_code):
    """Create a callable that executes a named JS function via mini-racer (V8)."""
    from py_mini_racer import MiniRacer

    ctx = MiniRacer()
    ctx.eval(js_code)

    def call(*args):
        if not args:
            return ctx.eval("{}()".format(func_name))
        args_json = json.dumps(args)
        return ctx.eval("{}(...{})".format(func_name, args_json))

    return call


def _ensure_js_runtime():
    """Lazily initialize JS runtime on first actual use."""
    global _dsl_to_workflow_js, _vega_to_dsl_js
    if _dsl_to_workflow_js is not None:
        return

    try:
        dsl_js_path = os.path.join(ROOT_DIR, "templates", "dist", "dsl-to-workflow.umd.js")
        vega_js_path = os.path.join(ROOT_DIR, "templates", "dist", "vega-to-dsl.umd.js")

        with open(dsl_js_path, "r", encoding="utf8") as f:
            _dsl_to_workflow_js = _make_js_callable("main", f.read())

        with open(vega_js_path, "r", encoding="utf8") as f:
            _vega_to_dsl_js = _make_js_callable("main", f.read())
    except ImportError:
        raise ImportError(_INSTALL_MSG)


def dsl_to_workflow(dsl: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_js_runtime()
    return json.loads(_dsl_to_workflow_js(json.dumps(dsl)))


def vega_to_dsl(vega_config: Dict[str, Any], fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    _ensure_js_runtime()
    return json.loads(
        _vega_to_dsl_js(json.dumps({"vl": vega_config, "allFields": fields, "visId": rand_str(6), "name": rand_str(6)}))
    )
