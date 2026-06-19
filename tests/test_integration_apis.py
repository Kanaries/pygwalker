import importlib
import json
import sys
from types import ModuleType
from types import SimpleNamespace

import pandas as pd
import pytest


_OPTIONAL_INTEGRATION_MODULES = [
    "anywidget",
    "marimo",
    "reflex",
    "streamlit",
    "streamlit.components",
    "streamlit.components.v1",
    "streamlit.components.v1.components",
    "pygwalker.api.anywidget",
    "pygwalker.api.marimo",
    "pygwalker.api.reflex",
    "pygwalker.api.streamlit",
    "pygwalker.communications.anywidget_comm",
    "pygwalker.communications.streamlit_comm",
    "pygwalker.services.anywidget_widget",
    "pygwalker.services.streamlit_components",
]

_OPTIONAL_PARENT_ATTRS = [
    ("pygwalker.api", "anywidget"),
    ("pygwalker.api", "marimo"),
    ("pygwalker.api", "reflex"),
    ("pygwalker.api", "streamlit"),
    ("pygwalker.communications", "anywidget_comm"),
    ("pygwalker.communications", "streamlit_comm"),
    ("pygwalker.services", "anywidget_widget"),
    ("pygwalker.services", "streamlit_components"),
    ("streamlit", "components"),
    ("streamlit.components", "v1"),
]


@pytest.fixture(autouse=True)
def restore_optional_integration_modules():
    missing = object()
    snapshot = {name: sys.modules.get(name, missing) for name in _OPTIONAL_INTEGRATION_MODULES}
    parent_snapshot = {}
    for module_name, attr_name in _OPTIONAL_PARENT_ATTRS:
        module = sys.modules.get(module_name)
        if module is None:
            parent_snapshot[(module_name, attr_name)] = (missing, missing)
        else:
            parent_snapshot[(module_name, attr_name)] = (module, getattr(module, attr_name, missing))
            if hasattr(module, attr_name):
                delattr(module, attr_name)

    for name in _OPTIONAL_INTEGRATION_MODULES:
        sys.modules.pop(name, None)

    yield
    for name in _OPTIONAL_INTEGRATION_MODULES:
        sys.modules.pop(name, None)
    for name, module in snapshot.items():
        if module is not missing:
            sys.modules[name] = module

    for (module_name, attr_name), (module, value) in parent_snapshot.items():
        if module is missing:
            continue
        if value is missing:
            if hasattr(module, attr_name):
                delattr(module, attr_name)
        else:
            setattr(module, attr_name, value)


class FakeWalker:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.gid = kwargs["gid"] or "generated"
        self.init_callback_calls = []
        self.props_calls = []
        self.render_calls = []
        FakeWalker.instances.append(self)

    def _get_props(self, env="", data_source=None, need_load_datas=False):
        self.props_calls.append((env, data_source, need_load_datas))
        return {
            "id": self.gid,
            "env": env,
            "dataSource": data_source,
        }

    def _init_callback(self, comm, preview_tool=None):
        self.init_callback_calls.append((comm, preview_tool))

    def _get_render_iframe(self, props, return_iframe=True, iframe_width=None, iframe_height=None):
        self.render_calls.append((props, return_iframe, iframe_width, iframe_height))
        return json.dumps(props, sort_keys=True)


def _reset_fake_walker():
    FakeWalker.instances = []


def test_gradio_api_builds_walker_and_registers_comm(monkeypatch, tmp_path):
    from pygwalker.api import gradio

    _reset_fake_walker()
    monkeypatch.setattr(gradio, "PygWalker", FakeWalker)
    comms = []

    class FakeGradioCommunication:
        def __init__(self, gid):
            self.gid = gid
            comms.append(self)

    monkeypatch.setattr(gradio, "GradioCommunication", FakeGradioCommunication)

    html = gradio.get_html_on_gradio(
        pd.DataFrame([{"city": "London"}]),
        gid="gradio",
        spec_path=str(tmp_path / "gradio_spec.json"),
        spec_io_mode="rw",
        computation="browser",
        default_tab="data",
    )

    walker = FakeWalker.instances[0]
    assert walker.kwargs["gid"] == "gradio"
    assert walker.kwargs["spec"] == str(tmp_path / "gradio_spec.json")
    assert walker.kwargs["use_save_tool"] is True
    assert walker.kwargs["kernel_computation"] is False
    assert walker.kwargs["default_tab"] == "data"
    assert walker.props_calls == [("gradio", None, False)]
    assert walker.init_callback_calls == [(comms[0], None)]
    assert json.loads(html)["communicationUrl"] == gradio.BASE_URL_PATH


def test_reflex_api_returns_html_component(monkeypatch):
    fake_reflex = SimpleNamespace(Component=object, html=lambda value: {"html": value})
    monkeypatch.setitem(sys.modules, "reflex", fake_reflex)
    reflex = importlib.reload(importlib.import_module("pygwalker.api.reflex"))

    _reset_fake_walker()
    monkeypatch.setattr(reflex, "PygWalker", FakeWalker)
    comms = []

    class FakeReflexCommunication:
        def __init__(self, gid):
            self.gid = gid
            comms.append(self)

    monkeypatch.setattr(reflex, "ReflexCommunication", FakeReflexCommunication)

    component = reflex.get_component(
        pd.DataFrame([{"city": "London"}]),
        gid="reflex",
        spec_io_mode="r",
        computation="kernel",
    )

    walker = FakeWalker.instances[0]
    assert walker.kwargs["gid"] == "reflex"
    assert walker.kwargs["use_save_tool"] is False
    assert walker.kwargs["kernel_computation"] is True
    assert walker.props_calls == [("reflex", None, False)]
    assert walker.init_callback_calls == [(comms[0], None)]
    assert json.loads(component["html"])["communicationUrl"] == reflex.BASE_URL_PATH


def test_anywidget_api_builds_widget_props_and_registers_comm(monkeypatch):
    _install_anywidget_stubs(monkeypatch)
    anywidget_api = importlib.reload(importlib.import_module("pygwalker.api.anywidget"))

    _reset_fake_walker()
    monkeypatch.setattr(anywidget_api, "PygWalker", FakeWalker)
    comms = []

    class FakeAnywidgetCommunication:
        def __init__(self, gid):
            self.gid = gid
            self.widgets = []
            comms.append(self)

        def register_widget(self, widget):
            self.widgets.append(widget)

    monkeypatch.setattr(anywidget_api, "AnywidgetCommunication", FakeAnywidgetCommunication)

    widget = anywidget_api.walk(
        pd.DataFrame([{"city": "London"}]),
        gid="anywidget",
        show_cloud_tool=True,
        computation="browser",
    )

    walker = FakeWalker.instances[0]
    assert walker.kwargs["gid"] == "anywidget"
    assert walker.kwargs["kernel_computation"] is False
    assert walker.kwargs["use_save_tool"] is True
    assert walker.kwargs["is_export_dataframe"] is True
    assert walker.props_calls == [("anywidget", [], False)]
    assert json.loads(widget.props)["env"] == "anywidget"
    assert comms[0].widgets == [widget]
    assert walker.init_callback_calls == [(comms[0], None)]


def test_anywidget_api_accepts_public_walker_object(monkeypatch):
    _install_anywidget_stubs(monkeypatch)
    anywidget_api = importlib.reload(importlib.import_module("pygwalker.api.anywidget"))
    walker_api = importlib.import_module("pygwalker.api.walker")

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    comms = []

    class FakeAnywidgetCommunication:
        def __init__(self, gid):
            self.gid = gid
            self.widgets = []
            comms.append(self)

        def register_widget(self, widget):
            self.widgets.append(widget)

    monkeypatch.setattr(anywidget_api, "AnywidgetCommunication", FakeAnywidgetCommunication)

    public_walker = walker_api.Walker(
        pd.DataFrame([{"city": "London"}]),
        gid="anywidget-core",
        computation="browser",
    )
    widget = anywidget_api.walk(public_walker)

    assert len(FakeWalker.instances) == 1
    assert public_walker.core.use_preview is False
    assert json.loads(widget.props)["env"] == "anywidget"
    assert comms[0].widgets == [widget]
    assert public_walker.core.init_callback_calls == [(comms[0], None)]


def test_anywidget_api_rejects_rebuilding_public_walker_object(monkeypatch, tmp_path):
    _install_anywidget_stubs(monkeypatch)
    anywidget_api = importlib.reload(importlib.import_module("pygwalker.api.anywidget"))
    walker_api = importlib.import_module("pygwalker.api.walker")

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    public_walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")

    with pytest.raises(ValueError, match="cannot apply construction parameters: spec_path"):
        anywidget_api.walk(public_walker, spec_path=str(tmp_path / "other.json"))


def test_anywidget_api_rejects_show_cloud_tool_false_alias_for_public_walker(monkeypatch):
    _install_anywidget_stubs(monkeypatch)
    anywidget_api = importlib.reload(importlib.import_module("pygwalker.api.anywidget"))
    walker_api = importlib.import_module("pygwalker.api.walker")

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    public_walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")

    with pytest.raises(ValueError, match="cannot apply construction parameters: show_cloud_tool"):
        anywidget_api.walk(public_walker, show_cloud_tool=0)


def test_anywidget_widget_service_registers_comm(monkeypatch):
    _install_anywidget_stubs(monkeypatch)
    anywidget_widget = importlib.reload(importlib.import_module("pygwalker.services.anywidget_widget"))

    class FakeWalkerForWidget:
        gid = "widget-core"

        def __init__(self):
            self.props_calls = []
            self.init_callback_calls = []

        def _get_props(self, env, data_source):
            self.props_calls.append((env, data_source))
            return {"id": self.gid, "env": env, "dataSource": data_source}

        def _init_callback(self, comm):
            self.init_callback_calls.append(comm)

    comms = []

    class FakeAnywidgetCommunication:
        def __init__(self, gid):
            self.gid = gid
            self.widgets = []
            comms.append(self)

        def register_widget(self, widget):
            self.widgets.append(widget)

    walker = FakeWalkerForWidget()
    widget = anywidget_widget.create_anywidget_for_walker(
        walker,
        env="anywidget",
        data_source=[],
        communication_cls=FakeAnywidgetCommunication,
    )

    assert json.loads(widget.props) == {"id": "widget-core", "env": "anywidget", "dataSource": []}
    assert walker.props_calls == [("anywidget", [])]
    assert comms[0].gid == "widget-core"
    assert comms[0].widgets == [widget]
    assert walker.init_callback_calls == [comms[0]]


def test_marimo_api_wraps_anywidget(monkeypatch):
    wrapped_widgets = []
    _install_anywidget_stubs(monkeypatch)
    monkeypatch.setitem(
        sys.modules,
        "marimo",
        SimpleNamespace(
            ui=SimpleNamespace(anywidget=lambda widget: wrapped_widgets.append(widget) or {"wrapped": widget})
        ),
    )
    marimo_api = importlib.reload(importlib.import_module("pygwalker.api.marimo"))

    _reset_fake_walker()
    monkeypatch.setattr(marimo_api, "PygWalker", FakeWalker)
    comms = []

    class FakeAnywidgetCommunication:
        def __init__(self, gid):
            self.gid = gid
            self.widgets = []
            comms.append(self)

        def register_widget(self, widget):
            self.widgets.append(widget)

    monkeypatch.setattr(marimo_api, "AnywidgetCommunication", FakeAnywidgetCommunication)

    result = marimo_api.walk(pd.DataFrame([{"city": "London"}]), gid="marimo")

    walker = FakeWalker.instances[0]
    assert walker.props_calls == [("marimo", [], False)]
    assert json.loads(wrapped_widgets[0].props)["env"] == "marimo"
    assert comms[0].widgets == wrapped_widgets
    assert walker.init_callback_calls == [(comms[0], None)]
    assert result == {"wrapped": wrapped_widgets[0]}


def test_marimo_api_accepts_public_walker_object(monkeypatch):
    wrapped_widgets = []
    _install_anywidget_stubs(monkeypatch)
    monkeypatch.setitem(
        sys.modules,
        "marimo",
        SimpleNamespace(
            ui=SimpleNamespace(anywidget=lambda widget: wrapped_widgets.append(widget) or {"wrapped": widget})
        ),
    )
    marimo_api = importlib.reload(importlib.import_module("pygwalker.api.marimo"))
    walker_api = importlib.import_module("pygwalker.api.walker")

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    comms = []

    class FakeAnywidgetCommunication:
        def __init__(self, gid):
            self.gid = gid
            self.widgets = []
            comms.append(self)

        def register_widget(self, widget):
            self.widgets.append(widget)

    monkeypatch.setattr(marimo_api, "AnywidgetCommunication", FakeAnywidgetCommunication)

    public_walker = walker_api.Walker(
        pd.DataFrame([{"city": "London"}]),
        gid="marimo-core",
        computation="browser",
    )
    result = marimo_api.walk(public_walker)

    assert len(FakeWalker.instances) == 1
    assert public_walker.core.use_preview is False
    assert json.loads(wrapped_widgets[0].props)["env"] == "marimo"
    assert comms[0].widgets == wrapped_widgets
    assert public_walker.core.init_callback_calls == [(comms[0], None)]
    assert result == {"wrapped": wrapped_widgets[0]}


def test_marimo_api_rejects_rebuilding_public_walker_object(monkeypatch, tmp_path):
    _install_anywidget_stubs(monkeypatch)
    monkeypatch.setitem(sys.modules, "marimo", SimpleNamespace(ui=SimpleNamespace(anywidget=lambda widget: widget)))
    marimo_api = importlib.reload(importlib.import_module("pygwalker.api.marimo"))
    walker_api = importlib.import_module("pygwalker.api.walker")

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    public_walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")

    with pytest.raises(ValueError, match="cannot apply construction parameters: spec_path"):
        marimo_api.walk(public_walker, spec_path=str(tmp_path / "other.json"))


def test_streamlit_html_builds_renderer_and_component_html(monkeypatch, tmp_path):
    _install_streamlit_stubs(monkeypatch)
    streamlit = importlib.reload(importlib.import_module("pygwalker.api.streamlit"))

    _reset_fake_walker()
    monkeypatch.setattr(streamlit, "PygWalker", FakeWalker)
    monkeypatch.setattr(streamlit, "init_streamlit_comm", lambda: None)
    monkeypatch.setattr(streamlit, "get_dataset_hash", lambda _dataset: "dataset-hash")
    monkeypatch.setattr(streamlit, "StreamlitCommunication", lambda gid: {"gid": gid})

    html = streamlit.get_streamlit_html(
        pd.DataFrame([{"city": "London"}]),
        gid=None,
        spec_path=str(tmp_path / "streamlit_spec.json"),
        spec_io_mode="rw",
        computation="cloud",
        mode="table",
        default_tab="data",
    )

    walker = FakeWalker.instances[0]
    assert walker.kwargs["gid"] == "dataset-hash"
    assert walker.kwargs["spec"] == str(tmp_path / "streamlit_spec.json")
    assert walker.kwargs["use_save_tool"] is True
    assert walker.kwargs["kernel_computation"] is False
    assert walker.kwargs["cloud_computation"] is True
    assert walker.kwargs["default_tab"] == "data"
    assert walker.init_callback_calls == [({"gid": "dataset-hash"}, None)]
    rendered_props = json.loads(html)
    assert rendered_props["env"] == "streamlit"
    assert rendered_props["communicationUrl"] == streamlit.BASE_URL_PATH
    assert rendered_props["gwMode"] == "table"


def test_streamlit_renderer_accepts_public_walker_object(monkeypatch):
    _install_streamlit_stubs(monkeypatch)
    streamlit = importlib.reload(importlib.import_module("pygwalker.api.streamlit"))
    walker_api = importlib.import_module("pygwalker.api.walker")

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    monkeypatch.setattr(streamlit, "init_streamlit_comm", lambda: None)
    monkeypatch.setattr(streamlit, "StreamlitCommunication", lambda gid: {"gid": gid})

    public_walker = walker_api.Walker(
        pd.DataFrame([{"city": "London"}]),
        gid="streamlit-core",
        computation="browser",
    )
    renderer = streamlit.StreamlitRenderer(public_walker)
    html = renderer._get_html(mode="table")

    assert len(FakeWalker.instances) == 1
    assert renderer.walker is public_walker.core
    assert public_walker.core.use_preview is False
    assert public_walker.core.is_export_dataframe is False
    assert public_walker.core.init_callback_calls == [({"gid": "streamlit-core"}, None)]
    rendered_props = json.loads(html)
    assert rendered_props["env"] == "streamlit"
    assert rendered_props["gwMode"] == "table"


def test_streamlit_renderer_rejects_rebuilding_public_walker_object(monkeypatch, tmp_path):
    _install_streamlit_stubs(monkeypatch)
    streamlit = importlib.reload(importlib.import_module("pygwalker.api.streamlit"))
    walker_api = importlib.import_module("pygwalker.api.walker")

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    monkeypatch.setattr(streamlit, "init_streamlit_comm", lambda: None)

    public_walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")

    with pytest.raises(ValueError, match="cannot apply construction parameters: spec_path"):
        streamlit.StreamlitRenderer(public_walker, spec_path=str(tmp_path / "other.json"))


def test_streamlit_html_accepts_public_walker_object(monkeypatch):
    _install_streamlit_stubs(monkeypatch)
    streamlit = importlib.reload(importlib.import_module("pygwalker.api.streamlit"))
    walker_api = importlib.import_module("pygwalker.api.walker")

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    monkeypatch.setattr(streamlit, "init_streamlit_comm", lambda: None)
    monkeypatch.setattr(streamlit, "StreamlitCommunication", lambda gid: {"gid": gid})

    public_walker = walker_api.Walker(
        pd.DataFrame([{"city": "London"}]),
        gid="streamlit-html",
        computation="browser",
    )
    html = streamlit.get_streamlit_html(public_walker, mode="table")

    assert len(FakeWalker.instances) == 1
    rendered_props = json.loads(html)
    assert rendered_props["env"] == "streamlit"
    assert rendered_props["gwMode"] == "table"


def test_webserver_walk_builds_walker_and_starts_server(monkeypatch):
    from pygwalker.api import webserver

    _reset_fake_walker()
    monkeypatch.setattr(webserver, "PygWalker", FakeWalker)
    starts = []
    monkeypatch.setattr(
        webserver,
        "_start_server",
        lambda walker, port, *, auto_open, auto_shutdown: starts.append((walker, port, auto_open, auto_shutdown)),
    )

    webserver.walk(
        pd.DataFrame([{"city": "London"}]),
        gid="server",
        port=8765,
        auto_open=True,
        auto_shutdown=True,
        computation="kernel",
    )

    walker = FakeWalker.instances[0]
    assert walker.kwargs["gid"] == "server"
    assert walker.kwargs["use_save_tool"] is True
    assert walker.kwargs["is_export_dataframe"] is True
    assert walker.kwargs["kernel_computation"] is True
    assert walker.kwargs["cloud_computation"] is False
    assert walker.kwargs["gw_mode"] == "explore"
    assert starts == [(walker, 8765, True, True)]


def test_webserver_walk_accepts_public_walker_object(monkeypatch):
    from pygwalker.api import webserver
    from pygwalker.api import walker as walker_api

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    starts = []
    monkeypatch.setattr(
        webserver,
        "_start_server",
        lambda walker, port, *, auto_open, auto_shutdown: starts.append((walker, port, auto_open, auto_shutdown)),
    )

    public_walker = walker_api.Walker(
        pd.DataFrame([{"city": "London"}]),
        gid="server-core",
        computation="browser",
    )
    webserver.walk(public_walker, port=8768, auto_open=True, auto_shutdown=True)

    assert len(FakeWalker.instances) == 1
    assert starts == [(public_walker.core, 8768, True, True)]


def test_webserver_walk_rejects_rebuilding_public_walker_object(monkeypatch, tmp_path):
    from pygwalker.api import webserver
    from pygwalker.api import walker as walker_api

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    public_walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")

    with pytest.raises(ValueError, match="cannot apply construction parameters: spec_path"):
        webserver.walk(public_walker, spec_path=str(tmp_path / "other.json"))


def test_webserver_walk_allows_none_cloud_computation_for_public_walker(monkeypatch):
    from pygwalker.api import webserver
    from pygwalker.api import walker as walker_api

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    starts = []
    monkeypatch.setattr(
        webserver,
        "_start_server",
        lambda walker, port, *, auto_open, auto_shutdown: starts.append((walker, port, auto_open, auto_shutdown)),
    )

    public_walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")
    webserver.walk(public_walker, cloud_computation=None)

    assert starts == [(public_walker.core, None, False, False)]


def test_webserver_walk_rejects_show_cloud_tool_true_alias_for_public_walker(monkeypatch):
    from pygwalker.api import webserver
    from pygwalker.api import walker as walker_api

    _reset_fake_walker()
    monkeypatch.setattr(walker_api, "PygWalker", FakeWalker)
    public_walker = walker_api.Walker(pd.DataFrame([{"city": "London"}]), computation="browser")

    with pytest.raises(ValueError, match="cannot apply construction parameters: show_cloud_tool"):
        webserver.walk(public_walker, show_cloud_tool=1)


def test_webserver_start_server_disables_preview(monkeypatch):
    from pygwalker.api import webserver

    class FakeServer:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def serve_forever(self):
            return None

    walker = SimpleNamespace(
        gid="server-preview",
        use_preview=True,
        init_callback_calls=[],
    )
    walker._init_callback = lambda comm, preview_tool=None: walker.init_callback_calls.append((comm, preview_tool))

    monkeypatch.setattr(webserver, "CustomTCPServer", FakeServer)

    webserver._start_server(walker, 8769, auto_open=False, auto_shutdown=False)

    assert walker.use_preview is False
    assert len(walker.init_callback_calls) == 1
    assert walker.init_callback_calls[0][1] is None


def test_webserver_render_builds_filter_renderer(monkeypatch):
    from pygwalker.api import webserver

    _reset_fake_walker()
    monkeypatch.setattr(webserver, "PygWalker", FakeWalker)
    starts = []
    monkeypatch.setattr(
        webserver,
        "_start_server",
        lambda walker, port, *, auto_open, auto_shutdown: starts.append((walker, port, auto_open, auto_shutdown)),
    )

    webserver.render(
        pd.DataFrame([{"city": "London"}]),
        spec="{}",
        port=8766,
        auto_open=False,
        auto_shutdown=True,
        computation="browser",
    )

    walker = FakeWalker.instances[0]
    assert walker.kwargs["spec"] == "{}"
    assert walker.kwargs["use_save_tool"] is False
    assert walker.kwargs["kernel_computation"] is False
    assert walker.kwargs["cloud_computation"] is False
    assert walker.kwargs["gw_mode"] == "filter_renderer"
    assert walker.kwargs["is_export_dataframe"] is True
    assert starts == [(walker, 8766, False, True)]


def test_webserver_table_builds_table_renderer(monkeypatch):
    from pygwalker.api import webserver

    _reset_fake_walker()
    monkeypatch.setattr(webserver, "PygWalker", FakeWalker)
    starts = []
    monkeypatch.setattr(
        webserver,
        "_start_server",
        lambda walker, port, *, auto_open, auto_shutdown: starts.append((walker, port, auto_open, auto_shutdown)),
    )

    with pytest.warns(DeprecationWarning, match="kernel_computation"):
        webserver.table(
            pd.DataFrame([{"city": "London"}]),
            port=8767,
            auto_open=True,
            auto_shutdown=False,
            kernel_computation=False,
        )

    walker = FakeWalker.instances[0]
    assert walker.kwargs["spec"] == ""
    assert walker.kwargs["use_save_tool"] is False
    assert walker.kwargs["gw_mode"] == "table"
    assert walker.kwargs["is_export_dataframe"] is True
    assert starts == [(walker, 8767, True, False)]


def _install_anywidget_stubs(monkeypatch):
    import traitlets

    class FakeAnyWidget(traitlets.HasTraits):
        pass

    monkeypatch.setitem(sys.modules, "anywidget", SimpleNamespace(AnyWidget=FakeAnyWidget))


def _install_streamlit_stubs(monkeypatch):
    fake_streamlit = ModuleType("streamlit")
    fake_streamlit.config = SimpleNamespace(get_option=lambda _name: "")
    fake_streamlit.cache_resource = lambda func: func

    fake_components = ModuleType("streamlit.components")
    fake_components_v1 = ModuleType("streamlit.components.v1")
    fake_components_v1.declare_component = lambda *_args, **_kwargs: lambda **component_kwargs: component_kwargs
    fake_components_module = ModuleType("streamlit.components.v1.components")
    fake_components_module.CustomComponent = object

    fake_streamlit.components = fake_components
    fake_components.v1 = fake_components_v1

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "streamlit.components", fake_components)
    monkeypatch.setitem(sys.modules, "streamlit.components.v1", fake_components_v1)
    monkeypatch.setitem(sys.modules, "streamlit.components.v1.components", fake_components_module)
