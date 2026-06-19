import pytest
import json
from pathlib import Path

from pygwalker.utils import frontend_assets


def test_frontend_toolchain_targets_vite_6():
    package_json = json.loads((Path(__file__).resolve().parents[1] / "app" / "package.json").read_text())

    assert package_json["devDependencies"]["vite"].startswith("^6.")
    assert package_json["devDependencies"]["@vitejs/plugin-react"].startswith("^4.")


def test_read_frontend_asset_reads_from_templates_dist(monkeypatch, tmp_path):
    asset_dir = tmp_path / "templates" / "dist"
    asset_dir.mkdir(parents=True)
    (asset_dir / "asset.js").write_text("console.log('ok');", encoding="utf-8")
    monkeypatch.setattr(frontend_assets, "ROOT_DIR", str(tmp_path))

    assert frontend_assets.read_frontend_asset("asset.js", encoding="utf-8") == "console.log('ok');"


def test_read_frontend_asset_reports_compile_command(monkeypatch, tmp_path):
    monkeypatch.setattr(frontend_assets, "ROOT_DIR", str(tmp_path))

    with pytest.raises(RuntimeError) as exc_info:
        frontend_assets.read_frontend_asset("missing.js")

    message = str(exc_info.value)
    assert "pygwalker/templates/dist/missing.js" in message
    assert "./scripts/compile.sh" in message
