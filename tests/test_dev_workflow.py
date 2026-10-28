import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from pygwalker.services import anywidget_widget
from scripts import dev


def test_dev_extra_declares_anywidget_hmr_watcher():
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    dev_dependencies = pyproject.partition("dev = [")[2].partition("]")[0]

    assert '"watchfiles>=0.18.0"' in dev_dependencies


def test_pygwalker_dev_mode_enables_anywidget_hmr(monkeypatch, tmp_path):
    bundle = tmp_path / "pygwalker-app.es.js"
    bundle.write_text("export function render() {}", encoding="utf-8")
    monkeypatch.setenv("PYGWALKER_DEV", "true")
    monkeypatch.delenv("ANYWIDGET_HMR", raising=False)
    monkeypatch.setattr(anywidget_widget, "frontend_asset_pathlib", lambda *_parts: bundle)

    assert anywidget_widget._resolve_widget_esm() == bundle
    assert os.environ["ANYWIDGET_HMR"] == "1"


@pytest.mark.parametrize(("child_code", "expected_code"), [(7, 7), (0, 1)])
def test_dev_stack_propagates_unexpected_service_exit(monkeypatch, tmp_path, child_code, expected_code):
    class StoppedService:
        def __init__(self, name, _argv, _cwd, _env, _log_path):
            self.name = name
            self.proc = SimpleNamespace(returncode=child_code)

        def start(self):
            return None

        def is_running(self):
            return False

        def stop(self):
            return None

    dev._shutting_down.clear()
    monkeypatch.setattr(dev, "Service", StoppedService)
    monkeypatch.setattr(dev, "_resolve_exe", lambda _name, _hint: "unused")
    monkeypatch.setattr(dev, "_install_signal_handlers", lambda: None)
    monkeypatch.setattr(dev.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["dev.py", "--no-jupyter", "--log-dir", str(tmp_path)],
    )

    try:
        assert dev.main() == expected_code
    finally:
        dev._shutting_down.clear()


def test_dev_stack_propagates_initial_frontend_build_failure(monkeypatch, tmp_path):
    started_services = []

    class StoppedFrontendService:
        def __init__(self, name, _argv, _cwd, _env, _log_path):
            self.name = name
            self.proc = SimpleNamespace(returncode=9 if name == "frontend" else None)

        def start(self):
            started_services.append(self.name)

        def is_running(self):
            return self.name != "frontend"

        def stop(self):
            return None

    dev._shutting_down.clear()
    monkeypatch.setattr(dev, "Service", StoppedFrontendService)
    monkeypatch.setattr(dev, "_resolve_exe", lambda _name, _hint: "unused")
    monkeypatch.setattr(dev, "_install_signal_handlers", lambda: None)
    monkeypatch.setattr(dev, "_wait_for_first_build", lambda _service: False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["dev.py", "--no-browser", "--log-dir", str(tmp_path)],
    )

    try:
        assert dev.main() == 9
        assert started_services == ["frontend"]
    finally:
        dev._shutting_down.clear()


def test_dev_stack_signal_shutdown_remains_successful(monkeypatch, tmp_path):
    class SignalledService:
        def __init__(self, name, _argv, _cwd, _env, _log_path):
            self.name = name
            self.proc = SimpleNamespace(returncode=None)

        def start(self):
            dev._shutting_down.set()

        def is_running(self):
            return True

        def stop(self):
            return None

    dev._shutting_down.clear()
    monkeypatch.setattr(dev, "Service", SignalledService)
    monkeypatch.setattr(dev, "_resolve_exe", lambda _name, _hint: "unused")
    monkeypatch.setattr(dev, "_install_signal_handlers", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["dev.py", "--no-jupyter", "--log-dir", str(tmp_path)],
    )

    try:
        assert dev.main() == 0
    finally:
        dev._shutting_down.clear()
