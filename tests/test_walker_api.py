import sys
from types import SimpleNamespace

import pandas as pd
import pytest

import pygwalker
from pygwalker.api import html
from pygwalker.api import walker as walker_api


class FakeCoreWalker:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.gid = kwargs["gid"] or "generated"
        self.kernel_computation = kwargs["kernel_computation"]
        self.cloud_computation = kwargs["cloud_computation"]
        self.display_calls = []
        FakeCoreWalker.instances.append(self)

    def display_on_jupyter_use_widgets(self, iframe_width=None, iframe_height=None):
        self.display_calls.append(("jupyter-widget", iframe_width, iframe_height))

    def display_on_jupyter_use_anywidget(self):
        self.display_calls.append(("jupyter-anywidget",))

    def display_on_jupyter(self):
        self.display_calls.append(("jupyter-inline",))

    def display_on_convert_html(self):
        self.display_calls.append(("jupyter-convert",))

    def to_html(self, iframe_width=None, iframe_height=None):
        return f"iframe:{iframe_width}:{iframe_height}"

    def to_html_without_iframe(self):
        return "html-without-iframe"


@pytest.fixture(autouse=True)
def reset_fake_core_walker():
    FakeCoreWalker.instances = []
    yield
    FakeCoreWalker.instances = []


def test_public_package_exports_walker():
    assert pygwalker.Walker is walker_api.Walker


def test_walker_getattr_does_not_recurse_before_core_is_assigned():
    walker = object.__new__(walker_api.Walker)

    with pytest.raises(AttributeError):
        getattr(walker, "missing")


def test_walker_builds_core_with_unified_options(monkeypatch, tmp_path):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)
    spec_path = tmp_path / "gw_config.json"
    spec_path.write_text('{"config":[],"chart_map":{},"workflow_list":[],"version":"0.5.0"}')

    walker = walker_api.Walker(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="api",
        spec_path=str(spec_path),
        spec_io_mode="rw",
        computation="browser",
        default_tab="data",
        appearance="light",
    )

    core = FakeCoreWalker.instances[0]
    assert walker.core is core
    assert core.kwargs["gid"] == "api"
    assert core.kwargs["spec"] == str(spec_path)
    assert core.kwargs["kernel_computation"] is False
    assert core.kwargs["cloud_computation"] is False
    assert core.kwargs["use_save_tool"] is True
    assert core.kwargs["default_tab"] == "data"
    assert core.kwargs["appearance"] == "light"


def test_walker_preserves_auto_kernel_detection_by_default(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    walker_api.Walker(pd.DataFrame([{"city": "London", "value": 1}]))

    assert FakeCoreWalker.instances[0].kwargs["kernel_computation"] is None


def test_walker_show_auto_uses_current_notebook_env(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)
    monkeypatch.setattr(walker_api, "get_current_env", lambda: "jupyter")

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")
    result = walker.show(iframe_width="640px", iframe_height="480px")

    assert result is walker
    assert FakeCoreWalker.instances[0].display_calls == [("jupyter-anywidget",)]


def test_walker_show_accepts_legacy_jupyter_widget_alias(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")
    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport.*0\\.7\\.0"):
        walker.show("JupyterWidget", iframe_width="640px", iframe_height="480px")

    assert FakeCoreWalker.instances[0].display_calls == [("jupyter-anywidget",)]


def test_walker_show_accepts_legacy_jupyter_env_alias(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")
    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport.*0\\.7\\.0"):
        walker.show("Jupyter")

    assert FakeCoreWalker.instances[0].display_calls == [("jupyter-anywidget",)]


def test_walker_show_warns_for_lowercase_legacy_jupyter_env(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")
    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport.*0\\.7\\.0"):
        walker.show("jupyter-widget", iframe_width="640px", iframe_height="480px")

    assert FakeCoreWalker.instances[0].display_calls == [("jupyter-anywidget",)]


def test_walker_show_accepts_jupyter_preview_alias(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)
    monkeypatch.setattr(
        FakeCoreWalker,
        "display_preview_on_jupyter",
        lambda self: self.display_calls.append(("jupyter-preview",)),
        raising=False,
    )

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")
    walker.show("JupyterPreview")

    assert FakeCoreWalker.instances[0].display_calls == [("jupyter-preview",)]


def test_walker_show_auto_uses_webserver_outside_notebooks(monkeypatch):
    starts = []
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)
    monkeypatch.setattr(walker_api, "get_current_env", lambda: "script")
    monkeypatch.setattr(walker_api.webserver, "_start_server", lambda *args, **kwargs: starts.append((args, kwargs)))

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")
    walker.show(port=8765, auto_open=False, auto_shutdown=False)

    assert starts == [((FakeCoreWalker.instances[0], 8765), {"auto_open": False, "auto_shutdown": False})]


@pytest.mark.parametrize("kwargs", [{"computation": "kernel"}, {"computation": "cloud"}])
def test_walker_static_html_rejects_live_computation(monkeypatch, kwargs):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), **kwargs)

    with pytest.raises(ValueError, match="Static HTML export does not support"):
        walker.to_html()


def test_to_html_adapter_accepts_walker_object(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")
    rendered = html.to_html(walker, width="640px", height="480px")

    assert rendered == "iframe:640px:480px"


def test_to_html_adapter_rejects_rebuilding_walker_object(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")

    with pytest.raises(ValueError, match="cannot apply construction parameters: spec_path"):
        html.to_html(walker, spec_path="other.json")


def test_to_html_adapter_preserves_walker_live_computation_error(monkeypatch):
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="kernel")

    with pytest.raises(ValueError, match="Static HTML export does not support kernel computation"):
        html.to_html(walker)


def test_walker_to_streamlit_reuses_constructor_options(monkeypatch):
    renderer_calls = []
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    class FakeStreamlitRenderer:
        def __init__(self, dataset, gid=None, **kwargs):
            renderer_calls.append((dataset, gid, kwargs))

    monkeypatch.setitem(
        sys.modules,
        "pygwalker.api.streamlit",
        SimpleNamespace(StreamlitRenderer=FakeStreamlitRenderer),
    )

    dataset = pd.DataFrame([{"city": "London"}])
    walker = walker_api.Walker(dataset, gid="streamlit", spec="{}", computation="browser")

    renderer = walker.to_streamlit(key="value")

    assert isinstance(renderer, FakeStreamlitRenderer)
    assert renderer_calls[0][0] is dataset
    assert renderer_calls[0][1] == "streamlit"
    assert renderer_calls[0][2]["spec"] == "{}"
    assert renderer_calls[0][2]["computation"] == "browser"
    assert "cloud_computation" not in renderer_calls[0][2]
    assert renderer_calls[0][2]["key"] == "value"


def test_walker_to_streamlit_maps_legacy_cloud_computation_and_drops_kernel_flags(monkeypatch):
    renderer_calls = []
    monkeypatch.setattr(walker_api, "PygWalker", FakeCoreWalker)

    class FakeStreamlitRenderer:
        def __init__(self, dataset, gid=None, **kwargs):
            renderer_calls.append((dataset, gid, kwargs))

    monkeypatch.setitem(
        sys.modules,
        "pygwalker.api.streamlit",
        SimpleNamespace(StreamlitRenderer=FakeStreamlitRenderer),
    )

    with pytest.warns(DeprecationWarning, match="deprecated") as warnings:
        walker = walker_api.Walker(
            pd.DataFrame([{"city": "London"}]),
            cloud_computation=True,
            kernel_computation=True,
            use_kernel_calc=True,
        )
    walker.to_streamlit()

    assert len(warnings) == 3
    assert renderer_calls[0][2]["computation"] == "cloud"
    assert renderer_calls[0][2]["kernel_computation"] is None
    assert renderer_calls[0][2]["use_kernel_calc"] is None
    assert "cloud_computation" not in renderer_calls[0][2]
