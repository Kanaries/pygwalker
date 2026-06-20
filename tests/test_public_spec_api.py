import json

import pytest

import pygwalker as pyg
from pygwalker import __version__
from pygwalker.services import spec as spec_service


def _legacy_spec():
    return {
        "config": [
            {
                "name": "Legacy chart",
                "config": {},
                "encodings": {
                    "dimensions": [
                        {
                            "fid": "date",
                            "name": "date",
                            "computed": True,
                            "expression": {
                                "params": [
                                    {"type": "field", "value": "date"},
                                    {"type": "offset", "value": -480},
                                ]
                            },
                        }
                    ],
                    "measures": [],
                },
                "visId": "legacy",
            }
        ],
        "chart_map": {},
        "workflow_list": [{"workflow": []}],
        "version": "0.4.7a5",
    }


def test_spec_migrate_updates_legacy_spec_json_to_current_version():
    migrated = pyg.spec.migrate(json.dumps(_legacy_spec()))

    chart = migrated["config"][0]
    field = chart["encodings"]["dimensions"][0]

    assert migrated["version"] == __version__
    assert migrated["workflow_list"] == [{"workflow": []}]
    assert chart["config"]["timezoneDisplayOffset"] == 0
    assert field["offset"] == 0
    assert field["expression"]["params"][1] == {"type": "offset", "value": 0}


def test_spec_migrate_accepts_existing_local_file_and_custom_version(tmp_path):
    spec_path = tmp_path / "legacy.json"
    spec_path.write_text(json.dumps(_legacy_spec()), encoding="utf-8")

    migrated = pyg.spec.migrate(str(spec_path), version="0.6.0")

    assert migrated["version"] == "0.6.0"
    assert migrated["config"][0]["name"] == "Legacy chart"


def test_spec_migrate_reads_32_char_hex_local_file_without_remote_lookup(tmp_path, monkeypatch):
    spec_path = tmp_path / "0123456789abcdef0123456789abcdef"
    spec_path.write_text(json.dumps(_legacy_spec()), encoding="utf-8")

    def fail_remote_lookup(config_id):
        raise AssertionError(f"unexpected remote lookup for {config_id}")

    monkeypatch.setattr(spec_service, "_get_spec_from_server", fail_remote_lookup)

    migrated = pyg.spec.migrate(str(spec_path))

    assert migrated["config"][0]["name"] == "Legacy chart"


def test_spec_migrate_rejects_missing_path_without_creating_file(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(ValueError, match="dict, list, JSON string, or existing local file path"):
        pyg.spec.migrate(str(missing_path))

    assert not missing_path.exists()


def test_spec_migrate_rejects_invalid_json_string():
    with pytest.raises(ValueError, match="spec is not a valid json"):
        pyg.spec.migrate("{not-valid-json")


def test_spec_migrate_rejects_json_scalar():
    with pytest.raises(ValueError, match="JSON object or array"):
        pyg.spec.migrate("42")


def test_spec_migrate_does_not_mutate_caller_spec():
    legacy = _legacy_spec()
    original = json.loads(json.dumps(legacy))

    migrated = pyg.spec.migrate(legacy)

    assert legacy == original
    assert migrated is not legacy
    assert migrated["config"][0]["config"]["timezoneDisplayOffset"] == 0
