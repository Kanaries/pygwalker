import inspect
from pathlib import Path

from pygwalker.api import jupyter


def _read_walk_api_table_params() -> list[str]:
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
    return [row.split("|")[1].strip().strip("`") for row in rows]


def test_readme_walk_api_table_matches_jupyter_walk_signature():
    signature_params = []
    for parameter in inspect.signature(jupyter.walk).parameters.values():
        if parameter.kind is inspect.Parameter.VAR_KEYWORD:
            signature_params.append(f"**{parameter.name}")
        else:
            signature_params.append(parameter.name)

    assert _read_walk_api_table_params() == signature_params
