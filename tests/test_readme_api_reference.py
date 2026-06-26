import ast
import inspect
from pathlib import Path

import pytest

from pygwalker.api import jupyter


TRANSLATED_README_NOTICE = (
    "This translation is community-maintained and may lag behind the [English README](../README.md). "
    "Treat the English README as the source of truth for API reference, installation, and development instructions."
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_walk_api_table_rows() -> list[dict[str, str]]:
    readme = REPO_ROOT / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines()

    heading_index = lines.index("### [pygwalker.walk](https://pygwalker-docs.vercel.app/api-reference/jupyter#walk)")
    table_lines = []
    for line in lines[heading_index + 1 :]:
        if not line.startswith("|"):
            if table_lines:
                break
            continue
        table_lines.append(line)

    rows = table_lines[2:]
    parsed_rows = []
    for row in rows:
        cells = [cell.strip().strip("`") for cell in row.split("|")[1:-1]]
        parsed_rows.append(
            {
                "parameter": cells[0],
                "type": cells[1],
                "default": cells[2],
                "description": cells[3],
            }
        )
    return parsed_rows


def _read_walk_api_table_params() -> list[str]:
    return [row["parameter"] for row in _read_walk_api_table_rows()]


def _format_signature_default(parameter: inspect.Parameter) -> str:
    if parameter.default is inspect.Parameter.empty:
        return "-"
    if parameter.default == "":
        return '""'
    return repr(parameter.default)


def _read_source_docstring(relative_path: str, qualified_name: str) -> str:
    source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    module = ast.parse(source)
    parts = qualified_name.split(".")

    if len(parts) == 1:
        for node in module.body:
            if isinstance(node, ast.FunctionDef) and node.name == parts[0]:
                docstring = ast.get_docstring(node)
                assert docstring is not None
                return docstring
    elif len(parts) == 2:
        for node in module.body:
            if isinstance(node, ast.ClassDef) and node.name == parts[0]:
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == parts[1]:
                        docstring = ast.get_docstring(child)
                        assert docstring is not None
                        return docstring

    raise AssertionError(f"Could not find docstring for {qualified_name} in {relative_path}")


def test_readme_walk_api_table_matches_jupyter_walk_signature():
    signature_params = []
    for parameter in inspect.signature(jupyter.walk).parameters.values():
        if parameter.kind is inspect.Parameter.VAR_KEYWORD:
            signature_params.append(f"**{parameter.name}")
        else:
            signature_params.append(parameter.name)

    assert _read_walk_api_table_params() == signature_params


def test_readme_walk_api_table_defaults_match_jupyter_walk_signature():
    table_defaults = {row["parameter"]: row["default"] for row in _read_walk_api_table_rows()}
    signature_defaults = {}
    for parameter in inspect.signature(jupyter.walk).parameters.values():
        name = f"**{parameter.name}" if parameter.kind is inspect.Parameter.VAR_KEYWORD else parameter.name
        signature_defaults[name] = _format_signature_default(parameter)

    assert table_defaults == signature_defaults


def test_readme_walk_api_table_documents_reusable_walker_input():
    dataset_row = next(row for row in _read_walk_api_table_rows() if row["parameter"] == "dataset")

    assert "Walker" in dataset_row["type"]
    assert "pyarrow.Table" in dataset_row["type"]


@pytest.mark.parametrize(
    ("relative_path", "qualified_name", "expected_fragments"),
    [
        ("pygwalker/api/adapter.py", "walk", ("pyarrow.Table", "pygwalker.Walker")),
        ("pygwalker/api/adapter.py", "render", ("pyarrow.Table",)),
        ("pygwalker/api/adapter.py", "table", ("pyarrow.Table",)),
        ("pygwalker/api/anywidget.py", "walk", ("pyarrow.Table", "pygwalker.Walker")),
        ("pygwalker/api/jupyter.py", "walk", ("pyarrow.Table", "pygwalker.Walker")),
        ("pygwalker/api/jupyter.py", "render", ("pyarrow.Table",)),
        ("pygwalker/api/jupyter.py", "table", ("pyarrow.Table",)),
        ("pygwalker/api/marimo.py", "walk", ("pyarrow.Table", "pygwalker.Walker")),
        ("pygwalker/api/webserver.py", "walk", ("pyarrow.Table", "pygwalker.Walker")),
        ("pygwalker/api/webserver.py", "render", ("pyarrow.Table",)),
        ("pygwalker/api/webserver.py", "table", ("pyarrow.Table",)),
        ("pygwalker/api/streamlit.py", "StreamlitRenderer.__init__", ("pyarrow.Table", "pygwalker.Walker")),
        ("pygwalker/api/streamlit.py", "get_streamlit_html", ("pyarrow.Table", "pygwalker.Walker")),
        ("pygwalker/api/gradio.py", "get_html_on_gradio", ("pyarrow.Table",)),
        ("pygwalker/api/component.py", "component", ("pyarrow.Table",)),
        ("pygwalker/api/kanaries_cloud.py", "create_cloud_dataset", ("pyarrow.Table",)),
        ("pygwalker/api/kanaries_cloud.py", "create_cloud_walker", ("pyarrow.Table",)),
        ("pygwalker/api/html.py", "to_html", ("pyarrow.Table", "pygwalker.Walker")),
        ("pygwalker/api/html.py", "to_table_html", ("pyarrow.Table",)),
        ("pygwalker/api/html.py", "to_render_html", ("pyarrow.Table",)),
        ("pygwalker/api/html.py", "to_chart_html", ("pyarrow.Table",)),
    ],
)
def test_public_api_docstrings_document_current_dataset_inputs(relative_path, qualified_name, expected_fragments):
    docstring = _read_source_docstring(relative_path, qualified_name)

    assert "pl.DataFrame | pd.DataFrame" not in docstring
    for fragment in expected_fragments:
        assert fragment in docstring


def test_readme_walk_api_table_marks_legacy_jupyter_envs_deprecated():
    env_row = next(row for row in _read_walk_api_table_rows() if row["parameter"] == "env")

    assert "JupyterAnywidget" in env_row["description"]
    assert "deprecated aliases to the anywidget transport" in env_row["description"]
    assert "PyGWalker 0.7.0" in env_row["description"]


def test_translated_readmes_defer_api_reference_to_english_readme():
    docs_dir = Path(__file__).resolve().parents[1] / "docs"

    translated_readmes = sorted(docs_dir.glob("README.*.md"))
    assert translated_readmes
    for readme in translated_readmes:
        assert TRANSLATED_README_NOTICE in readme.read_text(encoding="utf-8")


def test_translated_readmes_do_not_repeat_stale_api_parameters():
    docs_dir = Path(__file__).resolve().parents[1] / "docs"
    stale_parameters = {"hide_data_source_config", "use_preview"}

    translated_readmes = sorted(docs_dir.glob("README.*.md"))
    assert translated_readmes
    for readme in translated_readmes:
        source = readme.read_text(encoding="utf-8")
        for parameter in stale_parameters:
            assert parameter not in source
