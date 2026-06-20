import base64
from contextlib import nullcontext
import json
from types import SimpleNamespace
import urllib.parse
import zlib

import pandas as pd
import pyarrow as pa
import pytest
from duckdb import ParserException

from pygwalker import __version__
from pygwalker.api import adapter, html, jupyter
from pygwalker.api import pygwalker as pygwalker_module
from pygwalker.api.pygwalker import PygWalker
from pygwalker.communications.base import BaseCommunication
from pygwalker.errors import ErrorCode
from pygwalker.services import chart_export as chart_export_module
from pygwalker.services import data_bridge as data_bridge_module
from pygwalker.services import desktop_import as desktop_import_module
from pygwalker.services import jupyter_display as jupyter_display_module
from pygwalker.services import props_tracker as props_tracker_module
from pygwalker.services import render_manager as render_manager_module
from pygwalker.services.global_var import GlobalVarManager


def _expected_legacy_computation_warning(kwargs):
    if (
        kwargs.get("kernel_computation") is not None
        or kwargs.get("use_kernel_calc") is not None
        or kwargs.get("cloud_computation") is True
    ):
        return pytest.warns(DeprecationWarning, match="deprecated")
    return nullcontext()


def _make_walker(monkeypatch, **kwargs):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pygwalker_module, "get_local_user_id", lambda: "test-user")

    defaults = {
        "gid": "core",
        "dataset": pd.DataFrame(
            [
                {"city": "London", "value": 1},
                {"city": "Tokyo", "value": 2},
            ]
        ),
        "field_specs": [],
        "spec": "",
        "source_invoke_code": "",
        "theme_key": "g2",
        "appearance": "light",
        "show_cloud_tool": False,
        "use_preview": False,
        "kernel_computation": False,
        "cloud_computation": False,
        "use_save_tool": False,
        "is_export_dataframe": False,
        "kanaries_api_key": "",
        "default_tab": "vis",
        "gw_mode": "explore",
    }
    defaults.update(kwargs)
    return PygWalker(**defaults)


def _patch_cloud_computation_parser(monkeypatch):
    original_get_parser = data_bridge_module.get_parser
    uploaded = []

    class FakeCloudParser:
        data_size = 1
        raw_fields = [
            {"fid": "city", "name": "city", "semanticType": "nominal", "analyticType": "dimension"},
            {"fid": "value", "name": "value", "semanticType": "quantitative", "analyticType": "measure"},
        ]
        dataset_type = "cloud_dataset"

        def to_records(self, limit=None):
            return [{"city": "London", "value": 1}]

    def fake_get_parser(
        dataset,
        field_specs=None,
        infer_string_to_date=False,
        infer_number_to_dimension=True,
        other_params=None,
    ):
        if isinstance(dataset, str) and dataset == "cloud-dataset-id":
            return FakeCloudParser()
        return original_get_parser(
            dataset,
            field_specs,
            infer_string_to_date,
            infer_number_to_dimension,
            other_params,
        )

    def fake_create_cloud_dataset(self, data_parser, name, is_public, temporary):
        uploaded.append(
            {
                "data_parser": data_parser,
                "name": name,
                "is_public": is_public,
                "temporary": temporary,
            }
        )
        return "cloud-dataset-id"

    monkeypatch.setattr(data_bridge_module, "get_parser", fake_get_parser)
    monkeypatch.setattr(pygwalker_module.CloudService, "create_cloud_dataset", fake_create_cloud_dataset)
    return uploaded


def _chart_payload(title="Updated chart"):
    return {
        "charts": [
            {
                "rowIndex": 0,
                "colIndex": 0,
                "data": "data:image/png;base64,abc",
                "height": 100,
                "width": 200,
                "canvasHeight": 100,
                "canvasWidth": 200,
            }
        ],
        "singleChart": "data:image/png;base64,abc",
        "nRows": 1,
        "nCols": 1,
        "title": title,
    }


def test_pygwalker_props_expose_browser_data_path(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=False)

    props = walker._get_props(env="test", need_load_datas=True)

    assert props["id"] == "core"
    assert props["env"] == "test"
    assert props["dataSource"] == [
        {"city": "London", "value": 1},
        {"city": "Tokyo", "value": 2},
    ]
    assert props["len"] == 2
    assert props["needLoadDatas"] is True
    assert props["useKernelCalc"] is False
    assert props["parseDslType"] == "client"
    assert props["datasetType"] == "pandas_dataframe"
    assert props["hashcode"] == "test-user"


def test_pygwalker_props_expose_kernel_data_path(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)

    props = walker._get_props(env="test", data_source=[], need_load_datas=True)

    assert props["dataSource"] == []
    assert props["len"] == 0
    assert props["needLoadDatas"] is False
    assert props["useKernelCalc"] is True


def test_pygwalker_get_props_falls_back_without_props_builder(monkeypatch):
    track_calls = []
    monkeypatch.setattr(pygwalker_module, "get_local_user_id", lambda: "fallback-user")
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *args, **kwargs: track_calls.append((args, kwargs)))
    walker = PygWalker.__new__(PygWalker)
    walker.gid = "fallback"
    walker.data_bridge = SimpleNamespace(
        origin_data_source=[{"city": "London"}],
        field_specs=[{"fid": "city"}],
        kernel_computation=False,
        parse_dsl_type="client",
        dataset_type="pandas_dataframe",
        data_parser=SimpleNamespace(field_metas=[]),
    )
    walker.spec_manager = SimpleNamespace(
        vis_spec=[],
        spec_type="empty",
        chart_map={},
    )
    walker.theme_key = "g2"
    walker.appearance = "light"
    walker.source_invoke_code = ""
    walker.tunnel_id = "tunnel"
    walker.data_source_id = "data-source"
    walker.show_cloud_tool = False
    walker.use_save_tool = False
    walker.gw_mode = "explore"
    walker.other_props = {}
    walker.is_export_dataframe = False
    walker.default_tab = "vis"
    walker.cloud_computation = False
    walker.kanaries_api_key = ""

    props = walker._get_props("fallback-env")

    assert props["id"] == "fallback"
    assert props["hashcode"] == "fallback-user"
    assert props["dataSource"] == [{"city": "London"}]
    assert props["rawFields"] == [{"fid": "city", "offset": 0}]
    assert track_calls[0][0][0] == "invoke_props"


def test_props_tracker_tracks_expected_invocation_fields():
    track_calls = []
    tracker = props_tracker_module.PropsTracker(
        SimpleNamespace(kanaries_api_key="secret-token"),
        lambda event, props: track_calls.append((event, props)),
    )

    tracker.track_invocation(
        {
            "id": "core",
            "version": "0.5",
            "hashcode": "user",
            "themeKey": "g2",
            "dark": "light",
            "env": "jupyter",
            "specType": "empty",
            "needLoadDatas": True,
            "showCloudTool": False,
            "useKernelCalc": False,
            "useSaveTool": True,
            "parseDslType": "client",
            "gwMode": "explore",
            "datasetType": "pandas_dataframe",
            "defaultTab": "vis",
            "useCloudCalc": False,
            "dataSource": [{"city": "London"}],
            "rawFields": [{"fid": "city"}],
        }
    )

    assert track_calls == [
        (
            "invoke_props",
            {
                "id": "core",
                "version": "0.5",
                "hashcode": "user",
                "themeKey": "g2",
                "dark": "light",
                "env": "jupyter",
                "specType": "empty",
                "needLoadDatas": True,
                "showCloudTool": False,
                "useKernelCalc": False,
                "useSaveTool": True,
                "parseDslType": "client",
                "gwMode": "explore",
                "datasetType": "pandas_dataframe",
                "defaultTab": "vis",
                "useCloudCalc": False,
                "hasKanariesToken": True,
            },
        )
    ]


def test_render_manager_preview_handles_parser_exception_and_manual_gid(monkeypatch):
    captured = {}

    class FakeDataParser:
        def get_datas_by_payload(self, workflow):
            if workflow == "bad-workflow":
                raise ParserException("bad workflow")
            return [{"workflow": workflow}]

    def fake_render_preview(vis_spec, datas, theme_key, gid, appearance):
        captured.update(
            {
                "vis_spec": vis_spec,
                "datas": datas,
                "theme_key": theme_key,
                "gid": gid,
                "appearance": appearance,
            }
        )
        return "preview-html"

    monkeypatch.setattr(render_manager_module, "render_gw_preview_html", fake_render_preview)
    monkeypatch.setattr(render_manager_module, "rand_str", lambda: "-manual")

    walker = SimpleNamespace(
        workflow_list=["good-workflow", "bad-workflow"],
        data_parser=FakeDataParser(),
        vis_spec=[{"chart": "bar"}],
        theme_key="g2",
        gid="core",
        appearance="light",
    )

    html = render_manager_module.RenderManager(walker).get_preview_html(manual=True)

    assert html == "preview-html"
    assert captured == {
        "vis_spec": [{"chart": "bar"}],
        "datas": [[{"workflow": "good-workflow"}], []],
        "theme_key": "g2",
        "gid": "core-manual",
        "appearance": "light",
    }


def test_render_manager_chart_preview_uses_chart_indexed_workflow(monkeypatch):
    captured = {}

    class FakeDataParser:
        def get_datas_by_payload(self, workflow):
            assert workflow == "target-workflow"
            return [{"value": 1}]

    class FakeSpecManager:
        def get_chart_index(self, chart_name):
            assert chart_name == "Target chart"
            return 1

    def fake_render_chart_preview(**kwargs):
        captured.update(kwargs)
        return "chart-html"

    monkeypatch.setattr(render_manager_module, "render_gw_chart_preview_html", fake_render_chart_preview)

    walker = SimpleNamespace(
        workflow_list=["other-workflow", "target-workflow"],
        data_parser=FakeDataParser(),
        spec_manager=FakeSpecManager(),
        vis_spec=[{"chart": "other"}, {"chart": "target"}],
        theme_key="g2",
        appearance="light",
    )

    html = render_manager_module.RenderManager(walker).get_chart_preview_html(
        "Target chart",
        title="Chart title",
        desc="Chart desc",
    )

    assert html == "chart-html"
    assert captured == {
        "single_vis_spec": {"chart": "target"},
        "data": [{"value": 1}],
        "theme_key": "g2",
        "title": "Chart title",
        "desc": "Chart desc",
        "appearance": "light",
    }


def test_render_manager_chart_preview_returns_empty_for_mismatched_workflow_list():
    class FakeSpecManager:
        def get_chart_index(self, chart_name):
            assert chart_name == "Missing workflow"
            return 1

    walker = SimpleNamespace(
        workflow_list=["only-workflow"],
        data_parser=SimpleNamespace(get_datas_by_payload=lambda workflow: [{"value": 1}]),
        spec_manager=FakeSpecManager(),
        vis_spec=[{"chart": "only"}, {"chart": "missing-workflow"}],
        theme_key="g2",
        appearance="light",
    )

    assert render_manager_module.RenderManager(walker).get_chart_preview_html("Missing workflow", "Title", "Desc") == ""


def test_jupyter_display_manager_convert_html_displays_iframe():
    displayed = []
    walker = SimpleNamespace(
        _get_props=lambda env: {"env": env},
        _get_render_iframe=lambda props: f"iframe-{props['env']}",
    )

    jupyter_display_module.JupyterDisplayManager(walker, displayed.append).display_on_convert_html()

    assert displayed == ["iframe-jupyter"]


def test_jupyter_display_manager_uploads_large_classic_jupyter_data(monkeypatch):
    displayed = []
    upload_calls = []

    class FakeUploadTool:
        def run(self, **kwargs):
            upload_calls.append(kwargs)

    monkeypatch.setattr(jupyter_display_module, "get_max_limited_datas", lambda records, _limit: records[:1])
    monkeypatch.setattr(jupyter_display_module, "BatchUploadDatasToolOnJupyter", lambda: FakeUploadTool())
    monkeypatch.setattr(jupyter_display_module, "render_iframe_messages_html", lambda gid: f"messages-{gid}")

    walker = SimpleNamespace(
        gid="classic",
        origin_data_source=[{"city": "London"}, {"city": "Tokyo"}],
        data_source_id="data-source",
        tunnel_id="tunnel",
        _get_props=lambda env, data_source, need_load_datas: {
            "env": env,
            "dataSource": data_source,
            "needLoadDatas": need_load_datas,
        },
        _get_render_iframe=lambda props: f"iframe-{props['env']}-{props['needLoadDatas']}",
    )

    jupyter_display_module.JupyterDisplayManager(walker, displayed.append).display_on_jupyter()

    assert displayed == ["iframe-jupyter-True", "messages-classic"]
    assert upload_calls == [
        {
            "records": [{"city": "London"}, {"city": "Tokyo"}],
            "sample_data_count": 0,
            "data_source_id": "data-source",
            "gid": "classic",
            "tunnel_id": "tunnel",
        }
    ]


def test_chart_export_manager_exports_png(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b"png-bytes"

    monkeypatch.setattr(chart_export_module.urllib.request, "urlopen", lambda url: FakeResponse())
    walker = SimpleNamespace(
        _get_chart_by_name=lambda name: SimpleNamespace(single_chart=f"https://example.test/{name}.png")
    )

    assert chart_export_module.ChartExportManager(walker, lambda _: None).export_chart_png("Chart 1") == b"png-bytes"


def test_chart_export_manager_exports_svg_variants():
    encoded_svg = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="
    raw_svg = "<svg></svg>"

    encoded_walker = SimpleNamespace(
        _get_chart_by_name=lambda _name: SimpleNamespace(charts=[SimpleNamespace(data=encoded_svg)])
    )
    raw_walker = SimpleNamespace(
        _get_chart_by_name=lambda _name: SimpleNamespace(charts=[SimpleNamespace(data=raw_svg)])
    )

    assert (
        chart_export_module.ChartExportManager(encoded_walker, lambda _: None).export_chart_svg("Chart 1")
        == b"<svg></svg>"
    )
    assert (
        chart_export_module.ChartExportManager(raw_walker, lambda _: None).export_chart_svg("Chart 1") == b"<svg></svg>"
    )


def test_chart_export_manager_display_chart_uses_chart_name_as_default_title():
    displayed = []
    calls = []
    walker = SimpleNamespace(
        _get_gw_chart_preview_html=lambda chart_name, title, desc: calls.append((chart_name, title, desc)) or "html"
    )

    chart_export_module.ChartExportManager(walker, displayed.append).display_chart("Chart 1")

    assert calls == [("Chart 1", "Chart 1", "")]
    assert displayed == ["html"]


def test_chart_export_manager_get_single_chart_html_by_spec(monkeypatch):
    calls = []

    monkeypatch.setattr(chart_export_module, "dsl_to_workflow", lambda spec: calls.append(("workflow", spec)) or "wf")
    monkeypatch.setattr(
        chart_export_module,
        "render_gw_chart_preview_html",
        lambda **kwargs: calls.append(("render", kwargs)) or "chart-html",
    )

    walker = SimpleNamespace(
        data_parser=SimpleNamespace(
            get_datas_by_payload=lambda workflow: calls.append(("data", workflow)) or [{"x": 1}]
        ),
        theme_key="g2",
        appearance="light",
    )

    html = chart_export_module.ChartExportManager(walker, lambda _: None).get_single_chart_html_by_spec(
        spec={"mark": "bar"},
        title="Title",
        desc="Desc",
    )

    assert html == "chart-html"
    assert calls == [
        ("workflow", {"mark": "bar"}),
        ("data", "wf"),
        (
            "render",
            {
                "single_vis_spec": {"mark": "bar"},
                "data": [{"x": 1}],
                "theme_key": "g2",
                "title": "Title",
                "desc": "Desc",
                "appearance": "light",
            },
        ),
    ]


@pytest.mark.parametrize(
    ("dataset_type", "expected_parse_dsl_type"),
    [
        ("pandas_dataframe", "client"),
        ("connector_database", "server"),
        ("cloud_dataset", "server"),
    ],
)
def test_pygwalker_parse_dsl_type_tracks_dataset_location(
    dataset_type,
    expected_parse_dsl_type,
):
    walker = PygWalker.__new__(PygWalker)
    data_parser = SimpleNamespace(dataset_type=dataset_type)

    assert walker._get_parse_dsl_type(data_parser) == expected_parse_dsl_type


def test_pygwalker_data_bridge_property_setters_remain_writable(monkeypatch):
    walker = _make_walker(monkeypatch)
    data_parser = SimpleNamespace(dataset_type="custom")

    walker.data_parser = data_parser
    walker.kernel_computation = True
    walker.origin_data_source = [{"city": "Paris"}]
    walker.field_specs = [{"fid": "city"}]
    walker.parse_dsl_type = "server"
    walker.dataset_type = "custom_dataset"

    assert walker.data_bridge.data_parser is data_parser
    assert walker.data_bridge.kernel_computation is True
    assert walker.data_bridge.origin_data_source == [{"city": "Paris"}]
    assert walker.data_bridge.field_specs == [{"fid": "city"}]
    assert walker.data_bridge.parse_dsl_type == "server"
    assert walker.data_bridge.dataset_type == "custom_dataset"


def test_pygwalker_init_preserves_get_data_parser_override(monkeypatch):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    calls = []

    class FakeParser:
        data_size = 1
        raw_fields = [{"fid": "city"}]
        dataset_type = "pandas_dataframe"
        field_metas = []

        def to_records(self, limit=None):
            return [{"city": "London"}]

    class HookedPygWalker(PygWalker):
        def _get_data_parser(self, **kwargs):
            calls.append(kwargs)
            return FakeParser()

    walker = HookedPygWalker(
        gid="hooked",
        dataset=pd.DataFrame([{"city": "London"}]),
        field_specs=[],
        spec="",
        source_invoke_code="",
        theme_key="g2",
        appearance="light",
        show_cloud_tool=False,
        use_preview=False,
        kernel_computation=False,
        cloud_computation=False,
        use_save_tool=False,
        is_export_dataframe=False,
        kanaries_api_key="",
        default_tab="vis",
        gw_mode="explore",
    )

    assert len(calls) == 1
    assert calls[0]["dataset"].to_dict("records") == [{"city": "London"}]
    assert walker.data_parser.dataset_type == "pandas_dataframe"


def test_pygwalker_kernel_callbacks_register_data_query_endpoints(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    comm = BaseCommunication("core")

    walker._init_callback(comm)

    assert {"get_datas", "get_datas_by_payload"} <= set(comm._endpoint_map)


def test_pygwalker_kernel_data_query_callback_returns_records(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg(
        "get_datas",
        {"sql": "SELECT SUM(value) AS total FROM pygwalker_mid_table"},
    )

    assert response == {
        "code": 0,
        "data": {"datas": [{"total": 3}]},
        "message": "success",
    }


def test_pygwalker_kernel_data_query_callback_validates_payload(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("get_datas", {})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "sql" in response["message"]


def test_pygwalker_kernel_data_query_callback_rejects_unknown_fields(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("get_datas", {"sql": "SELECT 1", "unexpected": True})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "unexpected" in response["message"]


def test_base_communication_envelope_routes_valid_message(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg_envelope(
        {
            "action": "get_datas",
            "data": {"sql": "SELECT SUM(value) AS total FROM pygwalker_mid_table"},
            "gid": "core",
            "rid": "request-1",
        }
    )

    assert response == {
        "code": 0,
        "data": {"datas": [{"total": 3}]},
        "message": "success",
    }


def test_base_communication_envelope_defaults_missing_data(monkeypatch):
    walker = _make_walker(monkeypatch)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg_envelope({"action": "ping"})

    assert response == {"code": 0, "data": {}, "message": "success"}


def test_ping_callback_rejects_unknown_fields(monkeypatch):
    walker = _make_walker(monkeypatch)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("ping", {"unexpected": True})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "unexpected" in response["message"]


def test_base_communication_envelope_rejects_missing_action():
    comm = BaseCommunication("core")

    response = comm._receive_msg_envelope({"data": {}})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "action" in response["message"]


def test_base_communication_rejects_unknown_action_as_invalid_request():
    comm = BaseCommunication("core")

    response = comm._receive_msg("missing_endpoint", {})

    assert response == {
        "code": ErrorCode.INVALID_REQUEST,
        "data": None,
        "message": "Unknown action: missing_endpoint",
    }


def test_pygwalker_batch_payload_query_callback_validates_payload(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("batch_get_datas_by_payload", {"queryList": ["not-a-payload"]})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "queryList" in response["message"] or "query_list" in response["message"]


def test_pygwalker_payload_query_callback_rejects_unknown_nested_fields(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg(
        "get_datas_by_payload",
        {"payload": {"workflow": [{"type": "view"}], "unexpected": True}},
    )

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "unexpected" in response["message"]


def test_pygwalker_browser_callbacks_do_not_register_data_query_endpoints(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=False)
    comm = BaseCommunication("core")

    walker._init_callback(comm)

    assert {"get_latest_vis_spec", "request_data", "ping"} <= set(comm._endpoint_map)
    assert "get_datas" not in comm._endpoint_map
    assert "get_datas_by_payload" not in comm._endpoint_map


def test_pygwalker_get_latest_vis_spec_callback_rejects_unknown_fields(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=False)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("get_latest_vis_spec", {"unexpected": True})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "unexpected" in response["message"]


def test_pygwalker_request_data_callback_uploads_current_records(monkeypatch):
    upload_calls = []

    class FakeUploadTool:
        def __init__(self, comm):
            self.comm = comm

        def run(self, **kwargs):
            upload_calls.append(kwargs)

    monkeypatch.setattr(pygwalker_module, "BatchUploadDatasToolOnWidgets", FakeUploadTool)
    walker = _make_walker(monkeypatch, kernel_computation=False)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("request_data", {})

    assert response == {"code": 0, "data": {}, "message": "success"}
    assert upload_calls == [
        {
            "records": [
                {"city": "London", "value": 1},
                {"city": "Tokyo", "value": 2},
            ],
            "sample_data_count": 0,
            "data_source_id": walker.data_source_id,
        }
    ]


def test_pygwalker_request_data_callback_rejects_unknown_fields(monkeypatch):
    upload_calls = []

    class FakeUploadTool:
        def __init__(self, comm):
            self.comm = comm

        def run(self, **kwargs):
            upload_calls.append(kwargs)

    monkeypatch.setattr(pygwalker_module, "BatchUploadDatasToolOnWidgets", FakeUploadTool)
    walker = _make_walker(monkeypatch, kernel_computation=False)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("request_data", {"unexpected": True})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "unexpected" in response["message"]
    assert upload_calls == []


def test_pygwalker_update_spec_callback_updates_runtime_state(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)
    vis_spec = [{"name": "Updated chart", "encodings": {}}]
    workflow_list = [{"type": "filter"}]
    chart_data = _chart_payload()

    response = comm._receive_msg(
        "update_spec",
        {
            "visSpec": vis_spec,
            "workflowList": workflow_list,
            "chartData": chart_data,
        },
    )

    assert response == {"code": 0, "data": {}, "message": "success"}
    assert walker.vis_spec == vis_spec
    assert walker.workflow_list == workflow_list
    assert walker._chart_map["Updated chart"].title == "Updated chart"


def test_pygwalker_update_spec_callback_validates_payload(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("update_spec", {"visSpec": []})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "chartData" in response["message"] or "chart_data" in response["message"]


def test_pygwalker_update_spec_callback_validates_chart_data_shape(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg(
        "update_spec",
        {
            "visSpec": [{"name": "Broken chart", "encodings": {}}],
            "chartData": {"title": "Broken chart"},
        },
    )

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "singleChart" in response["message"] or "single_chart" in response["message"]


def test_pygwalker_update_spec_callback_rejects_extra_chart_data_fields(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)
    chart_data = _chart_payload("Extra chart")
    chart_data["mode"] = "explore"

    response = comm._receive_msg(
        "update_spec",
        {
            "visSpec": [{"name": "Extra chart", "encodings": {}}],
            "chartData": chart_data,
        },
    )

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "mode" in response["message"]


def test_pygwalker_update_spec_callback_defaults_missing_workflow_list(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)
    vis_spec = [{"name": "Default workflow chart", "encodings": {}}]

    response = comm._receive_msg(
        "update_spec",
        {
            "visSpec": vis_spec,
            "chartData": _chart_payload("Default workflow chart"),
        },
    )

    assert response == {"code": 0, "data": {}, "message": "success"}
    assert walker.vis_spec == vis_spec
    assert walker.workflow_list == []


def test_pygwalker_runtime_spec_properties_remain_writable(monkeypatch):
    walker = _make_walker(monkeypatch)
    vis_spec = [{"name": "Manual chart", "encodings": {}}]

    walker.spec_type = "manual"
    walker.spec_version = "0.6.0"
    walker.vis_spec = vis_spec
    walker.workflow_list = [{"workflow": []}]
    walker._chart_map = {}
    walker._chart_name_index_map = {"Manual chart": 0}

    assert walker.spec_type == "manual"
    assert walker.spec_version == "0.6.0"
    assert walker.vis_spec == vis_spec
    assert walker.workflow_list == [{"workflow": []}]
    assert walker._chart_map == {}
    assert walker._chart_name_index_map == {"Manual chart": 0}


def test_pygwalker_update_spec_callback_writes_json_file(monkeypatch, tmp_path):
    spec_path = tmp_path / "gw_config.json"
    spec_path.write_text(json.dumps({"config": [], "chart_map": {}, "workflow_list": [], "version": "0.5.0"}))
    walker = _make_walker(monkeypatch, spec=str(spec_path), use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)
    vis_spec = [{"name": "File chart", "encodings": {}}]
    workflow_list = [{"workflow": [{"type": "view"}]}]

    response = comm._receive_msg(
        "update_spec",
        {
            "visSpec": vis_spec,
            "workflowList": workflow_list,
            "chartData": _chart_payload("File chart"),
        },
    )

    assert response == {"code": 0, "data": {}, "message": "success"}
    assert json.loads(spec_path.read_text()) == {
        "config": vis_spec,
        "chart_map": {},
        "version": __version__,
        "workflow_list": workflow_list,
    }


def test_pygwalker_loads_saved_chart_map_from_spec(monkeypatch):
    chart_payload = _chart_payload("Saved chart")

    walker = _make_walker(
        monkeypatch,
        spec={
            "config": [],
            "chart_map": {"Saved chart": chart_payload},
            "workflow_list": [],
            "version": "0.5.0",
        },
    )

    assert walker.chart_list == ["Saved chart"]
    assert walker._get_chart_by_name("Saved chart").title == "Saved chart"


def test_pygwalker_to_code_exports_current_spec_state(monkeypatch):
    walker = _make_walker(monkeypatch)
    walker.vis_spec = [{"name": "Bob's chart", "encodings": {}}]
    walker.workflow_list = [{"workflow": [{"type": "view"}]}]
    walker.spec_version = "0.6.0"

    code = walker.to_code(dataset_name="source_df", variable_name="explorer")

    assert code.startswith("import pygwalker as pyg\n\n")
    assert code.endswith("explorer = pyg.walk(source_df, spec=spec)")

    namespace = {}
    exec(code.splitlines()[2], {}, namespace)
    assert json.loads(namespace["spec"]) == {
        "config": [{"name": "Bob's chart", "encodings": {}}],
        "chart_map": {},
        "version": "0.6.0",
        "workflow_list": [{"workflow": [{"type": "view"}]}],
    }


def test_pygwalker_to_code_can_omit_import_and_rejects_invalid_variable_name(monkeypatch):
    walker = _make_walker(monkeypatch)

    assert walker.to_code(include_import=False).startswith("spec = ")
    with pytest.raises(ValueError, match="variable_name"):
        walker.to_code(variable_name="not valid")
    with pytest.raises(ValueError, match="variable_name"):
        walker.to_code(variable_name="class")


def test_pygwalker_export_dataframe_callback_stores_last_dataframe(monkeypatch):
    previous_exported_dataframe = GlobalVarManager.last_exported_dataframe
    walker = _make_walker(monkeypatch, is_export_dataframe=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    try:
        response = comm._receive_msg(
            "export_dataframe_by_sql",
            {"sql": "SELECT city, value FROM pygwalker_mid_table WHERE value = 2"},
        )

        assert response == {"code": 0, "data": {}, "message": "success"}
        assert walker.last_exported_dataframe.to_dict("records") == [{"city": "Tokyo", "value": 2}]
        assert GlobalVarManager.last_exported_dataframe is walker.last_exported_dataframe
    finally:
        GlobalVarManager.last_exported_dataframe = previous_exported_dataframe


def test_pygwalker_export_dataframe_by_payload_callback_stores_last_dataframe(monkeypatch):
    previous_exported_dataframe = GlobalVarManager.last_exported_dataframe
    walker = _make_walker(monkeypatch, is_export_dataframe=True)
    calls = []
    walker.data_parser = SimpleNamespace(
        get_datas_by_payload=lambda payload: calls.append(payload) or [{"city": "London", "value": 1}]
    )
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    try:
        response = comm._receive_msg(
            "export_dataframe_by_payload",
            {"payload": {"workflow": [{"type": "view"}]}},
        )

        assert response == {"code": 0, "data": {}, "message": "success"}
        assert calls == [{"workflow": [{"type": "view"}]}]
        assert walker.last_exported_dataframe.to_dict("records") == [{"city": "London", "value": 1}]
        assert GlobalVarManager.last_exported_dataframe is walker.last_exported_dataframe
    finally:
        GlobalVarManager.last_exported_dataframe = previous_exported_dataframe


def test_pygwalker_batch_sql_callback_returns_records(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    calls = []
    walker.data_parser = SimpleNamespace(
        batch_get_datas_by_sql=lambda query_list: calls.append(query_list) or [[{"total": 3}]]
    )
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("batch_get_datas_by_sql", {"queryList": ["SELECT 1"]})

    assert response == {"code": 0, "data": {"datas": [[{"total": 3}]]}, "message": "success"}
    assert calls == [["SELECT 1"]]


def test_pygwalker_upload_spec_to_cloud_callback_writes_workspace_path(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    writes = []
    walker.cloud_service = SimpleNamespace(
        get_kanaries_user_info=lambda: {"workspaceName": "workspace"},
        write_config_to_cloud=lambda path, data: writes.append((path, json.loads(data))),
    )
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("upload_spec_to_cloud", {"newToken": "", "fileName": "chart.json"})

    assert response == {
        "code": 0,
        "data": {"specFilePath": "workspace/chart.json"},
        "message": "success",
    }
    assert writes == [
        (
            "workspace/chart.json",
            {
                "config": [],
                "chart_map": {},
                "workflow_list": [],
                "version": __version__,
            },
        )
    ]


def test_pygwalker_upload_spec_to_cloud_callback_validates_payload(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("upload_spec_to_cloud", {"newToken": ""})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "fileName" in response["message"] or "file_name" in response["message"]


def test_pygwalker_save_chart_callback_validates_and_stores_chart(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("save_chart", _chart_payload("Recovered chart"))

    assert response == {"code": 0, "data": {}, "message": "success"}
    assert walker.chart_list == ["Recovered chart"]
    assert walker._get_chart_by_name("Recovered chart").single_chart == "data:image/png;base64,abc"


def test_pygwalker_save_chart_callback_validates_payload(monkeypatch):
    walker = _make_walker(monkeypatch, use_save_tool=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("save_chart", {"title": "Broken chart"})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "singleChart" in response["message"] or "single_chart" in response["message"]


def test_pygwalker_cloud_text_callbacks_validate_payloads(monkeypatch):
    ask_calls = []
    chat_calls = []
    walker = _make_walker(
        monkeypatch,
        show_cloud_tool=True,
        custom_ask_callback=lambda metas, query: ask_calls.append((metas, query)) or {"chart": "bar"},
        custom_chat_callback=lambda metas, chats: chat_calls.append((metas, chats)) or {"chart": "line"},
    )
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    ask_response = comm._receive_msg("get_spec_by_text", {"metas": [{"fid": "city"}], "query": "show city"})
    chat_response = comm._receive_msg(
        "get_chart_by_chats",
        {"metas": [{"fid": "city"}], "chats": [{"role": "user", "content": "show city"}]},
    )
    invalid_response = comm._receive_msg("get_spec_by_text", {"metas": []})

    assert ask_response == {"code": 0, "data": {"data": {"chart": "bar"}}, "message": "success"}
    assert chat_response == {"code": 0, "data": {"data": {"chart": "line"}}, "message": "success"}
    assert ask_calls == [([{"fid": "city"}], "show city")]
    assert chat_calls == [([{"fid": "city"}], [{"role": "user", "content": "show city"}])]
    assert invalid_response["code"] == ErrorCode.INVALID_REQUEST
    assert "query" in invalid_response["message"]


def test_pygwalker_upload_cloud_chart_callback_validates_and_uploads(monkeypatch):
    upload_calls = []
    walker = _make_walker(monkeypatch, show_cloud_tool=True)
    walker.cloud_service = SimpleNamespace(
        upload_cloud_chart=lambda **kwargs: (
            upload_calls.append(kwargs) or {"chart_id": "chart-id", "dataset_id": "dataset-id"}
        )
    )
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg(
        "upload_to_cloud_charts",
        {
            "chartName": "Cloud chart",
            "datasetName": "Dataset",
            "isPublic": True,
            "visSpec": [{"name": "Cloud chart"}],
            "workflow": [{"type": "view"}],
        },
    )
    invalid_response = comm._receive_msg(
        "upload_to_cloud_charts",
        {
            "chartName": "Cloud chart",
            "datasetName": "Dataset",
            "isPublic": True,
            "visSpec": [{"name": "Cloud chart"}],
        },
    )

    assert response == {
        "code": 0,
        "data": {"chartId": "chart-id", "datasetId": "dataset-id"},
        "message": "success",
    }
    assert upload_calls == [
        {
            "data_parser": walker.data_parser,
            "chart_name": "Cloud chart",
            "dataset_name": "Dataset",
            "workflow": [{"type": "view"}],
            "spec_list": [{"name": "Cloud chart"}],
            "is_public": True,
        }
    ]
    assert invalid_response["code"] == ErrorCode.INVALID_REQUEST
    assert "workflow" in invalid_response["message"]


def test_pygwalker_upload_cloud_dashboard_callback_validates_and_uploads(monkeypatch):
    upload_calls = []
    walker = _make_walker(monkeypatch, show_cloud_tool=True)
    walker.cloud_service = SimpleNamespace(
        upload_cloud_dashboard=lambda **kwargs: (
            upload_calls.append(kwargs) or {"dashboard_id": "dashboard-id", "dataset_id": "dataset-id"}
        )
    )
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg(
        "upload_to_cloud_dashboard",
        {
            "chartName": "Dashboard",
            "datasetName": "Dataset",
            "isPublic": False,
            "isCreateDashboard": True,
            "visSpec": [{"name": "Chart A"}],
            "workflowList": [[{"type": "view"}]],
        },
    )
    invalid_response = comm._receive_msg(
        "upload_to_cloud_dashboard",
        {
            "chartName": "Dashboard",
            "datasetName": "Dataset",
            "isPublic": False,
            "visSpec": [{"name": "Chart A"}],
            "workflowList": [[{"type": "view"}]],
        },
    )

    assert response == {
        "code": 0,
        "data": {"dashboardId": "dashboard-id", "datasetId": "dataset-id"},
        "message": "success",
    }
    assert upload_calls == [
        {
            "data_parser": walker.data_parser,
            "dashboard_name": "Dashboard",
            "dataset_name": "Dataset",
            "workflow_list": [[{"type": "view"}]],
            "spec_list": [{"name": "Chart A"}],
            "is_public": False,
            "create_dashboard_flag": True,
            "appearance": walker.appearance,
        }
    ]
    assert invalid_response["code"] == ErrorCode.INVALID_REQUEST
    assert "isCreateDashboard" in invalid_response["message"] or "is_create_dashboard" in invalid_response["message"]


def test_pygwalker_open_in_desktop_callback_encodes_payload(monkeypatch):
    links = []
    monkeypatch.setattr(
        desktop_import_module.DesktopImportService,
        "_open_platform_link",
        staticmethod(lambda link: links.append(link)),
    )
    walker = _make_walker(monkeypatch)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg(
        "open_in_desktop",
        {
            "spec": [{"name": "Chart"}],
            "fields": [{"fid": "city"}],
        },
    )

    assert response == {"code": 0, "data": {}, "message": "success"}
    parsed = urllib.parse.urlparse(links[0])
    query = urllib.parse.parse_qs(parsed.query)

    def _decode_query_value(name):
        compressed = base64.b64decode(urllib.parse.unquote(query[name][0]))
        return json.loads(zlib.decompress(compressed).decode())

    assert parsed.scheme == "gw"
    assert parsed.netloc == "import"
    assert _decode_query_value("spec") == [{"name": "Chart"}]
    assert _decode_query_value("fields") == [{"fid": "city"}]
    assert _decode_query_value("data") == [
        {"city": "London", "value": 1},
        {"city": "Tokyo", "value": 2},
    ]


def test_pygwalker_open_in_desktop_callback_validates_payload(monkeypatch):
    links = []
    monkeypatch.setattr(
        desktop_import_module.DesktopImportService,
        "_open_platform_link",
        staticmethod(lambda link: links.append(link)),
    )
    walker = _make_walker(monkeypatch)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("open_in_desktop", {"spec": []})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "fields" in response["message"]
    assert links == []


@pytest.mark.parametrize(
    ("kwargs", "expected_kernel_computation"),
    [
        ({}, False),
        ({"kernel_computation": True}, True),
        ({"computation": "browser"}, False),
        ({"computation": "kernel"}, True),
        ({"computation": "cloud"}, False),
        ({"env": "JupyterConvert", "kernel_computation": False}, False),
    ],
)
def test_jupyter_walk_sets_pygwalker_kernel_computation_mode(
    monkeypatch,
    kwargs,
    expected_kernel_computation,
):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")
    monkeypatch.setattr(PygWalker, "display_on_jupyter_use_anywidget", lambda self: None)
    monkeypatch.setattr(PygWalker, "display_on_jupyter_use_widgets", lambda self: None)
    monkeypatch.setattr(PygWalker, "display_on_jupyter", lambda self: None)
    monkeypatch.setattr(PygWalker, "display_on_convert_html", lambda self: None)
    cloud_uploads = _patch_cloud_computation_parser(monkeypatch) if kwargs.get("computation") == "cloud" else []

    with _expected_legacy_computation_warning(kwargs):
        walker = jupyter.walk(
            pd.DataFrame([{"city": "London", "value": 1}]),
            gid="entry",
            **kwargs,
        )

    assert walker.kernel_computation is expected_kernel_computation
    if kwargs.get("computation") == "cloud":
        assert walker.cloud_computation is True
        assert walker.dataset_type == "cloud_dataset"
        assert len(cloud_uploads) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"computation": "kernel"},
        {"computation": "cloud"},
        {"kernel_computation": True},
        {"use_kernel_calc": True},
        {"cloud_computation": True},
    ],
)
def test_jupyter_walk_rejects_live_computation_for_convert_env(monkeypatch, kwargs):
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")

    with _expected_legacy_computation_warning(kwargs):
        with pytest.raises(ValueError, match="JupyterConvert/static HTML output does not support"):
            jupyter.walk(
                pd.DataFrame([{"city": "London", "value": 1}]),
                env="JupyterConvert",
                **kwargs,
            )


def test_jupyter_walk_accepts_explicit_spec_path(monkeypatch, tmp_path):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")
    monkeypatch.setattr(PygWalker, "display_on_jupyter_use_anywidget", lambda self: None)

    spec_path = tmp_path / "gw_config.json"
    spec_path.write_text(json.dumps({"config": [], "chart_map": {}, "workflow_list": [], "version": "0.5.0"}))

    walker = jupyter.walk(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="spec-path",
        spec_path=str(spec_path),
    )

    assert walker.spec_manager.spec == str(spec_path)
    assert walker.spec_manager.spec_type == "json_file"


def test_jupyter_walk_rejects_spec_and_spec_path(monkeypatch, tmp_path):
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")

    with pytest.raises(ValueError, match="Pass only one of `spec` or `spec_path`"):
        jupyter.walk(
            pd.DataFrame([{"city": "London", "value": 1}]),
            spec="{}",
            spec_path=str(tmp_path / "gw_config.json"),
        )


def test_jupyter_walk_accepts_public_walker_object(monkeypatch):
    import pygwalker

    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")

    display_calls = []
    monkeypatch.setattr(
        PygWalker,
        "display_on_jupyter_use_anywidget",
        lambda self: display_calls.append(self.gid),
    )

    public_walker = pygwalker.Walker(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="public-jupyter",
        computation="browser",
    )
    result = jupyter.walk(public_walker)

    assert result is public_walker.core
    assert display_calls == ["public-jupyter"]


def test_public_walker_accepts_empty_dataframe(monkeypatch):
    import pygwalker

    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)

    public_walker = pygwalker.Walker(
        pd.DataFrame({"city": pd.Series(dtype="object"), "value": pd.Series(dtype="int64")}),
        gid="public-empty",
        computation="browser",
    )

    assert public_walker.core.gid == "public-empty"
    assert public_walker.core.origin_data_source == []
    assert public_walker.core.dataset_type == "pandas_dataframe"
    assert public_walker.core.parse_dsl_type == "client"
    assert [field["fid"] for field in public_walker.core.field_specs] == ["city", "value"]


def test_public_walker_accepts_pyarrow_table(monkeypatch):
    import pygwalker

    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)

    public_walker = pygwalker.Walker(
        pa.table({"city": ["London"], "value": [1]}),
        gid="public-pyarrow",
        computation="browser",
    )

    assert public_walker.core.gid == "public-pyarrow"
    assert public_walker.core.origin_data_source == [{"city": "London", "value": 1}]
    assert public_walker.core.dataset_type == "pyarrow_table"
    assert public_walker.core.parse_dsl_type == "client"
    assert [field["fid"] for field in public_walker.core.field_specs] == ["city", "value"]


def test_jupyter_walk_public_walker_legacy_widget_env_warns_once(monkeypatch):
    from pygwalker.api.walker import Walker

    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")

    display_calls = []
    monkeypatch.setattr(
        PygWalker,
        "display_on_jupyter_use_widgets",
        lambda self, iframe_width=None, iframe_height=None: display_calls.append(
            (self.gid, iframe_width, iframe_height)
        ),
    )

    public_walker = Walker(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="public-legacy-widget",
        computation="browser",
    )

    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport") as warnings:
        result = jupyter.walk(public_walker, env="JupyterWidget")

    assert len(warnings) == 1
    assert result is public_walker.core
    assert display_calls == [("public-legacy-widget", None, None)]


def test_walker_show_legacy_inline_env_warns_once_with_core_display(monkeypatch):
    from pygwalker.api.walker import Walker

    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)

    display_calls = []
    public_walker = Walker(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="public-legacy-inline",
        computation="browser",
    )
    public_walker.core.jupyter_display_manager = SimpleNamespace(
        display_on_jupyter=lambda: display_calls.append(public_walker.core.gid)
    )

    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport") as warnings:
        result = public_walker.show("Jupyter")

    assert len(warnings) == 1
    assert result is public_walker
    assert display_calls == ["public-legacy-inline"]


def test_jupyter_walk_legacy_widget_env_uses_ipywidgets_transport(monkeypatch):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")

    display_calls = []
    monkeypatch.setattr(
        PygWalker,
        "display_on_jupyter_use_widgets",
        lambda self, iframe_width=None, iframe_height=None: display_calls.append(
            (self.gid, iframe_width, iframe_height)
        ),
    )

    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport"):
        walker = jupyter.walk(pd.DataFrame([{"city": "London", "value": 1}]), gid="legacy-widget", env="JupyterWidget")

    assert walker.gid == "legacy-widget"
    assert display_calls == [("legacy-widget", None, None)]


def test_jupyter_walk_legacy_inline_env_warns_and_uses_inline_transport(monkeypatch):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")

    display_calls = []
    monkeypatch.setattr(
        jupyter_display_module.JupyterDisplayManager,
        "display_on_jupyter",
        lambda self: display_calls.append(self.walker.gid),
    )

    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport") as warnings:
        walker = jupyter.walk(pd.DataFrame([{"city": "London", "value": 1}]), gid="legacy-inline", env="Jupyter")

    assert len(warnings) == 1
    assert walker.gid == "legacy-inline"
    assert display_calls == ["legacy-inline"]


def test_core_legacy_jupyter_display_methods_warn(monkeypatch):
    inline_calls = []
    widget_calls = []
    walker = _make_walker(monkeypatch, gid="core-legacy")
    walker.jupyter_display_manager = SimpleNamespace(
        display_on_jupyter=lambda: inline_calls.append(walker.gid),
        display_on_jupyter_use_widgets=lambda iframe_width=None, iframe_height=None: widget_calls.append(
            (iframe_width, iframe_height)
        ),
    )

    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport"):
        walker.display_on_jupyter()
    with pytest.warns(DeprecationWarning, match="legacy Jupyter transport"):
        walker.display_on_jupyter_use_widgets("640px", "480px")

    assert inline_calls == ["core-legacy"]
    assert widget_calls == [("640px", "480px")]


def test_display_on_jupyter_anywidget_sends_browser_data(monkeypatch):
    from pygwalker.services import anywidget_widget

    displayed = []
    created = []
    monkeypatch.setattr(pygwalker_module, "display_html", lambda widget: displayed.append(widget))
    monkeypatch.setattr(
        anywidget_widget,
        "create_anywidget_for_walker",
        lambda walker, *, env, data_source: created.append((walker, env, data_source)) or "widget",
    )

    walker = _make_walker(monkeypatch, kernel_computation=False, cloud_computation=False, use_preview=True)
    walker.display_on_jupyter_use_anywidget()

    assert walker.use_preview is False
    assert created == [(walker, "anywidget", walker.origin_data_source)]
    assert displayed == ["widget"]


def test_display_on_jupyter_anywidget_uses_comm_data_for_live_computation(monkeypatch):
    from pygwalker.services import anywidget_widget

    displayed = []
    created = []
    monkeypatch.setattr(pygwalker_module, "display_html", lambda widget: displayed.append(widget))
    monkeypatch.setattr(
        anywidget_widget,
        "create_anywidget_for_walker",
        lambda walker, *, env, data_source: created.append((walker, env, data_source)) or "widget",
    )

    walker = _make_walker(monkeypatch, kernel_computation=True, cloud_computation=False, use_preview=True)
    walker.display_on_jupyter_use_anywidget()

    assert walker.use_preview is False
    assert created == [(walker, "anywidget", [])]
    assert displayed == ["widget"]


def test_display_on_jupyter_anywidget_sends_cloud_mode_data(monkeypatch):
    from pygwalker.services import anywidget_widget

    displayed = []
    created = []
    cloud_uploads = _patch_cloud_computation_parser(monkeypatch)
    monkeypatch.setattr(pygwalker_module, "display_html", lambda widget: displayed.append(widget))
    monkeypatch.setattr(
        anywidget_widget,
        "create_anywidget_for_walker",
        lambda walker, *, env, data_source: created.append((walker, env, data_source)) or "widget",
    )

    walker = _make_walker(monkeypatch, kernel_computation=False, cloud_computation=True, use_preview=True)
    walker.display_on_jupyter_use_anywidget()

    assert walker.use_preview is False
    assert walker.dataset_type == "cloud_dataset"
    assert len(cloud_uploads) == 1
    assert created == [(walker, "anywidget", walker.origin_data_source)]
    assert displayed == ["widget"]


def test_jupyter_walk_public_walker_rejects_rebuilding_params(monkeypatch, tmp_path):
    from pygwalker.api.walker import Walker

    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")

    public_walker = Walker(pd.DataFrame([{"city": "London", "value": 1}]), computation="browser")

    with pytest.raises(ValueError, match="cannot apply construction parameters: spec_path"):
        jupyter.walk(public_walker, spec_path=str(tmp_path / "other.json"))


def test_jupyter_walk_public_walker_uses_convert_guard(monkeypatch):
    from pygwalker.api.walker import Walker

    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: True)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "")

    public_walker = Walker(pd.DataFrame([{"city": "London", "value": 1}]), computation="kernel")

    with pytest.raises(ValueError, match="JupyterConvert/static HTML output does not support kernel computation"):
        jupyter.walk(public_walker)


def test_jupyter_walk_public_walker_uses_preview_env(monkeypatch):
    from pygwalker.api.walker import Walker

    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jupyter, "check_kaggle", lambda: False)
    monkeypatch.setattr(jupyter, "check_convert", lambda: False)
    monkeypatch.setattr(jupyter, "get_kaggle_run_type", lambda: "batch")
    monkeypatch.setattr(jupyter, "adjust_kaggle_default_font_size", lambda: None)

    display_calls = []
    monkeypatch.setattr(PygWalker, "display_preview_on_jupyter", lambda self: display_calls.append(self.gid))

    public_walker = Walker(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="public-preview",
        computation="browser",
    )
    result = jupyter.walk(public_walker)

    assert result is public_walker.core
    assert display_calls == ["public-preview"]


def test_to_html_returns_iframe_for_pygwalker_static_export(monkeypatch):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pygwalker_module, "get_local_user_id", lambda: "test-user")

    rendered = html.to_html(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="static",
        appearance="light",
        width="640px",
        height="480px",
    )

    assert 'id="gwalker-static"' in rendered
    assert 'width="640px"' in rendered
    assert 'height="480px"' in rendered
    assert "srcdoc=" in rendered
    assert "eval(script)" not in rendered
    assert "URL.createObjectURL" in rendered


def test_to_html_accepts_pyarrow_table(monkeypatch):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pygwalker_module, "get_local_user_id", lambda: "test-user")

    rendered = html.to_html(
        pa.table({"city": ["London"], "value": [1]}),
        gid="static-pyarrow",
        computation="browser",
    )

    assert 'id="gwalker-static-pyarrow"' in rendered
    assert "srcdoc=" in rendered


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kernel_computation": True},
        {"cloud_computation": True},
        {"use_kernel_calc": True},
        {"computation": "kernel"},
        {"computation": "cloud"},
    ],
)
def test_to_html_rejects_live_computation_modes(kwargs):
    with pytest.raises(ValueError, match="Static HTML export does not support kernel or cloud computation"):
        html.to_html(pd.DataFrame([{"city": "London", "value": 1}]), **kwargs)


def test_to_html_rejects_invalid_computation_mode():
    with pytest.raises(ValueError, match="`computation` must be one of"):
        html.to_html(pd.DataFrame([{"city": "London", "value": 1}]), computation="server")


def test_to_html_allows_disabled_computation_kwargs(monkeypatch):
    monkeypatch.setattr(pygwalker_module, "check_update", lambda: None)
    monkeypatch.setattr(pygwalker_module, "track_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pygwalker_module, "get_local_user_id", lambda: "test-user")

    rendered = html.to_html(
        pd.DataFrame([{"city": "London", "value": 1}]),
        kernel_computation=False,
        cloud_computation=False,
        use_kernel_calc=None,
        computation="browser",
    )

    assert 'id="gwalker-' in rendered
    assert "srcdoc=" in rendered


@pytest.mark.parametrize(
    ("runtime_env", "expected_backend"),
    [
        ("jupyter", "jupyter"),
        ("script", "webserver"),
    ],
)
def test_public_walk_routes_pygwalker_to_environment_backend(
    monkeypatch,
    runtime_env,
    expected_backend,
):
    calls = []

    def fake_jupyter_walk(*args, **kwargs):
        calls.append(("jupyter", args, kwargs))
        return "jupyter-walker"

    def fake_webserver_walk(*args, **kwargs):
        calls.append(("webserver", args, kwargs))
        return "webserver-walker"

    monkeypatch.setattr(adapter, "get_current_env", lambda: runtime_env)
    monkeypatch.setattr(adapter.jupyter, "walk", fake_jupyter_walk)
    monkeypatch.setattr(adapter.webserver, "walk", fake_webserver_walk)

    result = adapter.walk(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="entry",
        spec_path="adapter_spec.json",
        computation="kernel",
    )

    assert result == f"{expected_backend}-walker"
    assert [call[0] for call in calls] == [expected_backend]
    assert calls[0][2]["spec_path"] == "adapter_spec.json"
    assert calls[0][2]["computation"] == "kernel"
    if expected_backend == "webserver":
        assert calls[0][2]["auto_open"] is True
        assert calls[0][2]["auto_shutdown"] is True


def test_public_walk_forwards_legacy_kernel_flag_to_webserver(monkeypatch):
    calls = []

    def fake_webserver_walk(*args, **kwargs):
        calls.append(("webserver", args, kwargs))
        return "webserver-walker"

    monkeypatch.setattr(adapter, "get_current_env", lambda: "script")
    monkeypatch.setattr(adapter.webserver, "walk", fake_webserver_walk)

    result = adapter.walk(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="entry",
        use_kernel_calc=True,
    )

    assert result == "webserver-walker"
    assert calls[0][2]["use_kernel_calc"] is True
