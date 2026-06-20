from typing import Dict, List, Any
import atexit
import json

from pygwalker.utils.frontend_assets import read_frontend_asset
from .randoms import rand_str

_dsl_to_workflow_js = None  # type: Optional[Callable]
_vega_to_dsl_js = None  # type: Optional[Callable]

_INSTALL_MSG = (
    "Static HTML chart export requires a JavaScript runtime.\n"
    "Install with: pip install pygwalker[export]\n"
    "Or manually: pip install mini-racer"
)


class _MiniRacerCallable:
    def __init__(self, func_name: str, js_code: str):
        from py_mini_racer import MiniRacer

        self._func_name = func_name
        self._ctx = MiniRacer()
        self._ctx.eval(js_code)

    def __call__(self, *args):
        if not args:
            return self._ctx.eval("{}()".format(self._func_name))
        args_json = json.dumps(args)
        return self._ctx.eval("{}(...{})".format(self._func_name, args_json))

    def close(self):
        if self._ctx is not None:
            self._ctx.close()
            self._ctx = None


def _make_js_callable(func_name, js_code):
    """Create a callable that executes a named JS function via mini-racer (V8)."""
    return _MiniRacerCallable(func_name, js_code)


def _close_js_runtime():
    global _dsl_to_workflow_js, _vega_to_dsl_js
    for runtime in (_dsl_to_workflow_js, _vega_to_dsl_js):
        if runtime is not None and hasattr(runtime, "close"):
            runtime.close()
    _dsl_to_workflow_js = None
    _vega_to_dsl_js = None


def _ensure_js_runtime():
    """Lazily initialize JS runtime on first actual use."""
    global _dsl_to_workflow_js, _vega_to_dsl_js
    if _dsl_to_workflow_js is not None:
        return

    try:
        _dsl_to_workflow_js = _make_js_callable("main", read_frontend_asset("dsl-to-workflow.umd.js"))
        _vega_to_dsl_js = _make_js_callable("main", read_frontend_asset("vega-to-dsl.umd.js"))
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


atexit.register(_close_js_runtime)
