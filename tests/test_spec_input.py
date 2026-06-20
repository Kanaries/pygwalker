import os

import pandas as pd
import pytest

from pygwalker.utils.spec import resolve_spec_input


def test_resolve_spec_input_uses_legacy_spec_when_no_spec_path():
    assert resolve_spec_input("{}", None) == "{}"


def test_resolve_spec_input_accepts_explicit_spec_path(tmp_path):
    path = tmp_path / "chart.json"

    assert resolve_spec_input("", path) == os.fspath(path)


def test_resolve_spec_input_accepts_pathlike_legacy_spec(tmp_path):
    path = tmp_path / "chart.json"

    assert resolve_spec_input(path, None) == os.fspath(path)


def test_resolve_spec_input_rejects_spec_and_spec_path_together(tmp_path):
    with pytest.raises(ValueError, match="Pass only one of `spec` or `spec_path`"):
        resolve_spec_input("{}", tmp_path / "chart.json")


def test_resolve_spec_input_rejects_array_like_spec_without_ambiguous_truth_value(tmp_path):
    with pytest.raises(ValueError, match="Pass only one of `spec` or `spec_path`"):
        resolve_spec_input(pd.Series(["{}"]), tmp_path / "chart.json")
