import ast
import re
from pathlib import Path


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


def _typescript_interface_keys(repo_root: Path, interface_name: str) -> set[str]:
    source = (repo_root / "app/src/interfaces/index.ts").read_text(encoding="utf-8")
    match = re.search(rf"export interface {interface_name} \{{([\s\S]*?)\n\}}", source)
    if match is None:
        raise AssertionError(f"Could not find {interface_name} interface")
    return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\??:", match.group(1), re.MULTILINE))


def test_frontend_props_interface_covers_python_props_builder():
    repo_root = Path(__file__).resolve().parents[1]

    assert _props_builder_keys(repo_root) - _app_props_keys(repo_root) == set()


def test_frontend_comm_maps_cover_python_comm_handler_endpoints():
    repo_root = Path(__file__).resolve().parents[1]
    endpoints = _comm_handler_endpoints(repo_root)

    assert _typescript_interface_keys(repo_root, "ICommRequestMap") == endpoints
    assert _typescript_interface_keys(repo_root, "ICommResponseMap") == endpoints


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
