import ast
import re
from pathlib import Path

from pydantic import BaseModel

from pygwalker.communications import protocol


PYTHON_REQUEST_MODEL_TS_TYPES = {
    "EmptyRequest": "ICommEmptyRequest",
    "SqlQueryRequest": "ICommSqlQueryRequest",
    "PayloadQueryRequest": "ICommPayloadQueryRequest",
    "BatchSqlQueryRequest": "ICommBatchQueryRequest<string>",
    "BatchPayloadQueryRequest": "ICommBatchQueryRequest<IDataQueryPayload>",
    "UploadSpecToCloudRequest": "ICommUploadSpecToCloudRequest",
    "SaveChartRequest": "ICommSaveChartRequest",
    "UpdateSpecRequest": "ICommUpdateSpecRequest",
    "AskSpecRequest": "ICommAskSpecRequest",
    "ChatChartRequest": "ICommChatChartRequest",
    "OpenDesktopRequest": "ICommOpenDesktopRequest",
    "UploadCloudChartRequest": "ICommUploadCloudChartRequest",
    "UploadCloudDashboardRequest": "ICommUploadCloudDashboardRequest",
}

PROTOCOL_MODEL_TS_INTERFACES = {
    protocol.CommMessageRequest: "ICommEnvelope",
    protocol.CommResponse: "ICommResponse",
    protocol.EmptyRequest: "ICommEmptyRequest",
    protocol.SqlQueryRequest: "ICommSqlQueryRequest",
    protocol.PayloadQueryRequest: "ICommPayloadQueryRequest",
    protocol.BatchSqlQueryRequest: "ICommBatchQueryRequest",
    protocol.BatchPayloadQueryRequest: "ICommBatchQueryRequest",
    protocol.UploadSpecToCloudRequest: "ICommUploadSpecToCloudRequest",
    protocol.ChartImageRequest: "ICommChartImageRequest",
    protocol.SaveChartRequest: "ICommSaveChartRequest",
    protocol.UpdateSpecRequest: "ICommUpdateSpecRequest",
    protocol.AskSpecRequest: "ICommAskSpecRequest",
    protocol.ChatChartRequest: "ICommChatChartRequest",
    protocol.OpenDesktopRequest: "ICommOpenDesktopRequest",
    protocol.UploadCloudChartRequest: "ICommUploadCloudChartRequest",
    protocol.UploadCloudDashboardRequest: "ICommUploadCloudDashboardRequest",
    protocol.EmptyResponse: "ICommEmptyResponse",
    protocol.LatestVisSpecResponse: "ICommLatestVisSpecResponse",
    protocol.DataRowsResponse: "ICommDataRowsResponse",
    protocol.BatchDataRowsResponse: "ICommBatchDataRowsResponse",
    protocol.UploadSpecToCloudResponse: "ICommUploadSpecToCloudResponse",
    protocol.CloudCallbackResponse: "ICommCloudCallbackResponse",
    protocol.UploadCloudChartResponse: "ICommUploadCloudChartResponse",
    protocol.UploadCloudDashboardResponse: "ICommUploadCloudDashboardResponse",
}


def _props_builder_keys(repo_root: Path) -> set[str]:
    source = (repo_root / "pygwalker/services/props_builder.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    for class_node in module.body:
        if not isinstance(class_node, ast.ClassDef) or class_node.name != "PropsBuilder":
            continue
        for method_node in class_node.body:
            if not isinstance(method_node, ast.FunctionDef) or method_node.name != "build":
                continue
            for node in ast.walk(method_node):
                if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                    return {
                        key.value
                        for key in node.value.keys
                        if isinstance(key, ast.Constant) and isinstance(key.value, str)
                    }
    raise AssertionError("Could not find PropsBuilder.build return keys")


def _app_props_keys(repo_root: Path) -> set[str]:
    source = (repo_root / "app/src/interfaces/index.ts").read_text(encoding="utf-8")
    match = re.search(r"export interface IAppProps \{([\s\S]*?)\n\}", source)
    if match is None:
        raise AssertionError("Could not find IAppProps interface")
    return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\??:", match.group(1), re.MULTILINE))


def _comm_handler_endpoints(repo_root: Path) -> set[str]:
    source = (repo_root / "pygwalker/services/comm_handler.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    for class_node in module.body:
        if not isinstance(class_node, ast.ClassDef) or class_node.name != "CommHandler":
            continue
        for method_node in class_node.body:
            if not isinstance(method_node, ast.FunctionDef) or method_node.name != "register":
                continue
            endpoints = set()
            for node in ast.walk(method_node):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in {"register", "_register_request"}:
                    continue
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    endpoints.add(node.args[0].value)
            return endpoints
    raise AssertionError("Could not find CommHandler.register endpoints")


def _comm_handler_request_models(repo_root: Path) -> dict[str, str]:
    source = (repo_root / "pygwalker/services/comm_handler.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    for class_node in module.body:
        if not isinstance(class_node, ast.ClassDef) or class_node.name != "CommHandler":
            continue
        for method_node in class_node.body:
            if not isinstance(method_node, ast.FunctionDef) or method_node.name != "register":
                continue
            endpoints = {}
            for node in ast.walk(method_node):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute) or node.func.attr != "_register_request":
                    continue
                if len(node.args) < 2:
                    continue
                endpoint_node, model_node = node.args[0], node.args[1]
                if isinstance(endpoint_node, ast.Constant) and isinstance(endpoint_node.value, str):
                    if isinstance(model_node, ast.Name):
                        endpoints[endpoint_node.value] = model_node.id
            return endpoints
    raise AssertionError("Could not find CommHandler.register request models")


def _comm_handler_register_calls(repo_root: Path) -> list[ast.Call]:
    source = (repo_root / "pygwalker/services/comm_handler.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    for class_node in module.body:
        if not isinstance(class_node, ast.ClassDef) or class_node.name != "CommHandler":
            continue
        for method_node in class_node.body:
            if isinstance(method_node, ast.FunctionDef) and method_node.name == "register":
                return [node for node in ast.walk(method_node) if isinstance(node, ast.Call)]
    raise AssertionError("Could not find CommHandler.register")


def _typescript_interface_keys(repo_root: Path, interface_name: str) -> set[str]:
    source = (repo_root / "app/src/interfaces/index.ts").read_text(encoding="utf-8")
    match = re.search(rf"export interface {interface_name} \{{([\s\S]*?)\n\}}", source)
    if match is None:
        raise AssertionError(f"Could not find {interface_name} interface")
    return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\??:", match.group(1), re.MULTILINE))


def _typescript_shape_keys(repo_root: Path, type_name: str) -> set[str]:
    source = (repo_root / "app/src/interfaces/index.ts").read_text(encoding="utf-8")
    empty_interface_pattern = rf"export interface {type_name}(?:<[^>]+>)? \{{\}}"
    if re.search(empty_interface_pattern, source) is not None:
        return set()

    interface_match = re.search(rf"export interface {type_name}(?:<[^>]+>)? \{{([\s\S]*?)\n\}}", source)
    if interface_match is not None:
        return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\??:", interface_match.group(1), re.MULTILINE))

    empty_alias_pattern = rf"export type {type_name} = Record<string, never>;"
    if re.search(empty_alias_pattern, source) is not None:
        return set()

    raise AssertionError(f"Could not find TypeScript shape for {type_name}")


def _typescript_map_values(repo_root: Path, interface_name: str) -> dict[str, str]:
    source = (repo_root / "app/src/interfaces/index.ts").read_text(encoding="utf-8")
    match = re.search(rf"export interface {interface_name} \{{([\s\S]*?)\n\}}", source)
    if match is None:
        raise AssertionError(f"Could not find {interface_name} interface")
    return dict(
        re.findall(
            r"^\s*([A-Za-z_][A-Za-z0-9_]*):\s*([^;]+);",
            match.group(1),
            re.MULTILINE,
        )
    )


def _pydantic_alias_keys(model_cls: type[BaseModel]) -> set[str]:
    fields = getattr(model_cls, "model_fields", None)
    if fields is not None:
        return {field.alias or name for name, field in fields.items()}
    return {field.alias or name for name, field in model_cls.__fields__.items()}


def test_frontend_props_interface_covers_python_props_builder():
    repo_root = Path(__file__).resolve().parents[1]

    assert _props_builder_keys(repo_root) - _app_props_keys(repo_root) == set()


def test_frontend_comm_maps_cover_python_comm_handler_endpoints():
    repo_root = Path(__file__).resolve().parents[1]
    endpoints = _comm_handler_endpoints(repo_root)

    assert _typescript_interface_keys(repo_root, "ICommRequestMap") == endpoints
    assert _typescript_interface_keys(repo_root, "ICommResponseMap") == endpoints


def test_frontend_comm_request_map_uses_types_matching_python_request_models():
    repo_root = Path(__file__).resolve().parents[1]
    request_models = _comm_handler_request_models(repo_root)
    request_map = _typescript_map_values(repo_root, "ICommRequestMap")

    assert {
        endpoint: PYTHON_REQUEST_MODEL_TS_TYPES[model_name] for endpoint, model_name in request_models.items()
    } == request_map


def test_frontend_protocol_interfaces_match_pydantic_aliases():
    repo_root = Path(__file__).resolve().parents[1]

    for model_cls, interface_name in PROTOCOL_MODEL_TS_INTERFACES.items():
        assert _typescript_shape_keys(repo_root, interface_name) == _pydantic_alias_keys(model_cls)


def test_comm_handler_register_uses_typed_request_models():
    repo_root = Path(__file__).resolve().parents[1]
    raw_register_calls = []
    untyped_request_calls = []

    for call in _comm_handler_register_calls(repo_root):
        if not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr == "register":
            raw_register_calls.append(call.lineno)
        if call.func.attr != "_register_request":
            continue
        if len(call.args) < 2 or not isinstance(call.args[1], ast.Name) or not call.args[1].id.endswith("Request"):
            untyped_request_calls.append(call.lineno)

    assert raw_register_calls == []
    assert untyped_request_calls == []


def test_frontend_dev_typescript_source_maps_are_enabled():
    repo_root = Path(__file__).resolve().parents[1]
    tsconfig = (repo_root / "app/tsconfig.json").read_text(encoding="utf-8")

    assert '"sourceMap": true' in tsconfig
    assert '"sourceMap": false' not in tsconfig


def test_frontend_tracker_loads_segment_only_after_events_opt_in():
    repo_root = Path(__file__).resolve().parents[1]
    tracker_source = (repo_root / "app/src/utils/tracker.ts").read_text(encoding="utf-8")
    app_source = (repo_root / "app/src/index.tsx").read_text(encoding="utf-8")

    assert "@segment/analytics-next" not in tracker_source
    assert "cdn.segment.com/analytics.js/v1/" in tracker_source
    assert 'tracker.setOpen(userConfig.privacy === "events")' in app_source


def test_frontend_modals_are_lazy_loaded_from_entrypoint():
    repo_root = Path(__file__).resolve().parents[1]
    app_source = (repo_root / "app/src/index.tsx").read_text(encoding="utf-8")

    modal_paths = [
        "./components/initModal",
        "./components/uploadSpecModal",
        "./components/uploadChartModal",
        "./components/codeExportModal",
    ]
    for modal_path in modal_paths:
        static_import_pattern = rf"import\s+[^;\n]+?\s+from\s+[\"']{re.escape(modal_path)}[\"']"

        assert re.search(static_import_pattern, app_source) is None
        assert f'import "{modal_path}"' not in app_source
        assert f"import '{modal_path}'" not in app_source
        assert f'import("{modal_path}")' in app_source


def test_frontend_save_payload_strips_graphic_walker_export_fields():
    repo_root = Path(__file__).resolve().parents[1]
    save_source = (repo_root / "app/src/utils/save.ts").read_text(encoding="utf-8")

    assert "Promise<ICommSaveChartRequest>" in save_source
    assert "...chartData" not in save_source
    assert "canvas: () => null" not in save_source
