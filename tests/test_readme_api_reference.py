import inspect
from pathlib import Path

from pygwalker.api import jupyter


TRANSLATED_README_NOTICE = (
    "This translation is community-maintained and may lag behind the [English README](../README.md). "
    "Treat the English README as the source of truth for API reference, installation, and development instructions."
)


def _read_walk_api_table_rows() -> list[dict[str, str]]:
    readme = Path(__file__).resolve().parents[1] / "README.md"
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


def test_readme_walk_api_table_marks_legacy_jupyter_envs_deprecated():
    env_row = next(row for row in _read_walk_api_table_rows() if row["parameter"] == "env")

    assert "JupyterAnywidget" in env_row["description"]
    assert "deprecated legacy transports" in env_row["description"]


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
