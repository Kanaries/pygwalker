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


def test_frontend_props_interface_covers_python_props_builder():
    repo_root = Path(__file__).resolve().parents[1]

    assert _props_builder_keys(repo_root) - _app_props_keys(repo_root) == set()
