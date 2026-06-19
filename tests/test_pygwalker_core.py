import base64
import json
from types import SimpleNamespace
import urllib.parse
import zlib

import pandas as pd
import pytest

from pygwalker import __version__
from pygwalker.api import adapter, html, jupyter
from pygwalker.api import pygwalker as pygwalker_module
from pygwalker.api.pygwalker import PygWalker
from pygwalker.communications.base import BaseCommunication
from pygwalker.errors import ErrorCode
from pygwalker.services import comm_handler as comm_handler_module
from pygwalker.services.global_var import GlobalVarManager


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


def test_pygwalker_batch_payload_query_callback_validates_payload(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=True)
    comm = BaseCommunication("core")
    walker._init_callback(comm)

    response = comm._receive_msg("batch_get_datas_by_payload", {"queryList": ["not-a-payload"]})

    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert "queryList" in response["message"] or "query_list" in response["message"]


def test_pygwalker_browser_callbacks_do_not_register_data_query_endpoints(monkeypatch):
    walker = _make_walker(monkeypatch, kernel_computation=False)
    comm = BaseCommunication("core")

    walker._init_callback(comm)

    assert {"get_latest_vis_spec", "request_data", "ping"} <= set(comm._endpoint_map)
    assert "get_datas" not in comm._endpoint_map
    assert "get_datas_by_payload" not in comm._endpoint_map


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

    assert response == {"code": 0, "data": None, "message": "success"}
    assert walker.vis_spec == vis_spec
    assert walker.workflow_list == workflow_list
    assert walker._chart_map["Updated chart"].title == "Updated chart"


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

    assert response == {"code": 0, "data": None, "message": "success"}
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

        assert response == {"code": 0, "data": None, "message": "success"}
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

        assert response == {"code": 0, "data": None, "message": "success"}
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


def test_pygwalker_open_in_desktop_callback_encodes_payload(monkeypatch):
    links = []
    monkeypatch.setattr(comm_handler_module.CommHandler, "_open_protocol", lambda _self, link: links.append(link))
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

    assert response == {"code": 0, "data": None, "message": "success"}
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


@pytest.mark.parametrize(
    ("kwargs", "expected_kernel_computation"),
    [
        ({}, False),
        ({"kernel_computation": True}, True),
        ({"env": "JupyterConvert", "kernel_computation": True}, False),
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
    monkeypatch.setattr(PygWalker, "display_on_jupyter_use_widgets", lambda self: None)
    monkeypatch.setattr(PygWalker, "display_on_jupyter", lambda self: None)
    monkeypatch.setattr(PygWalker, "display_on_convert_html", lambda self: None)

    walker = jupyter.walk(
        pd.DataFrame([{"city": "London", "value": 1}]),
        gid="entry",
        **kwargs,
    )

    assert walker.kernel_computation is expected_kernel_computation


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
        kernel_computation=True,
    )

    assert result == f"{expected_backend}-walker"
    assert [call[0] for call in calls] == [expected_backend]
    if expected_backend == "webserver":
        assert calls[0][2]["auto_open"] is True
        assert calls[0][2]["auto_shutdown"] is True
