import pytest

from pygwalker.errors import PrivacyError
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.spec import get_spec_json


@pytest.mark.parametrize(
    "spec",
    [
        "ksf://workspace/spec.json",
        "https://example.test/spec.json",
        "a" * 32,
    ],
)
def test_get_spec_json_rejects_remote_sources_in_offline_mode(spec):
    previous_privacy = GlobalVarManager.privacy
    GlobalVarManager.privacy = "offline"

    try:
        with pytest.raises(PrivacyError, match="privacy policy"):
            get_spec_json(spec)
    finally:
        GlobalVarManager.privacy = previous_privacy


def test_get_spec_json_reports_invalid_json_file(tmp_path):
    spec_path = tmp_path / "broken.json"
    spec_path.write_text("{not-valid-json", encoding="utf-8")

    with pytest.raises(ValueError, match="spec is not a valid json"):
        get_spec_json(str(spec_path))


def test_get_spec_json_rejects_ambiguous_long_file_name():
    with pytest.raises(ValueError, match="Spec file name too long"):
        get_spec_json("x" * 201)
