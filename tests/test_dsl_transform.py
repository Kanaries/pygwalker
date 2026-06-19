from unittest import mock
import builtins

import pytest

import pygwalker.utils.dsl_transform as mod
from pygwalker.utils.dsl_transform import dsl_to_workflow, vega_to_dsl


def _reset_runtime():
    """Reset the lazy-initialized JS runtime so tests are independent."""
    mod._dsl_to_workflow_js = None
    mod._vega_to_dsl_js = None


def test_dsl_to_workflow_returns_valid_workflow():
    _reset_runtime()
    result = dsl_to_workflow({})
    assert "workflow" in result
    assert isinstance(result["workflow"], list)


def test_dsl_to_workflow_with_fields():
    _reset_runtime()
    spec = {
        "encodings": {
            "dimensions": [{"fid": "a", "name": "a", "semanticType": "nominal", "analyticType": "dimension"}],
            "measures": [{"fid": "b", "name": "b", "semanticType": "quantitative", "analyticType": "measure"}],
        }
    }
    result = dsl_to_workflow(spec)
    assert "workflow" in result


def test_vega_to_dsl_returns_expected_keys():
    _reset_runtime()
    vega_spec = {
        "mark": "bar",
        "encoding": {
            "x": {"field": "a", "type": "nominal"},
            "y": {"field": "b", "type": "quantitative"},
        },
    }
    fields = [
        {"fid": "a", "name": "a", "analyticType": "dimension", "semanticType": "nominal"},
        {"fid": "b", "name": "b", "analyticType": "measure", "semanticType": "quantitative"},
    ]
    result = vega_to_dsl(vega_spec, fields)
    assert "config" in result
    assert "encodings" in result


def test_import_error_when_no_js_runtime():
    _reset_runtime()
    original_import = builtins.__import__

    def block_mini_racer(name, *args, **kwargs):
        if name == "py_mini_racer":
            raise ImportError("mocked")
        return original_import(name, *args, **kwargs)

    with mock.patch("builtins.__import__", side_effect=block_mini_racer):
        with pytest.raises(ImportError, match="pip install pygwalker\\[export\\]"):
            dsl_to_workflow({})


def test_runtime_initialized_only_once():
    _reset_runtime()
    original = mod._make_js_callable
    call_count = [0]

    def counting_make(*args, **kwargs):
        call_count[0] += 1
        return original(*args, **kwargs)

    with mock.patch.object(mod, "_make_js_callable", side_effect=counting_make):
        dsl_to_workflow({})
        dsl_to_workflow({})
    # _make_js_callable is called twice during init (once per UMD file), but only on first call
    assert call_count[0] == 2
