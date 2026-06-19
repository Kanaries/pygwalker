from pathlib import Path


def _extract_extra(pyproject_text: str, extra_name: str) -> list[str]:
    start = pyproject_text.index(f"{extra_name} = [")
    end = pyproject_text.index("]", start)
    return [line.strip().strip('",') for line in pyproject_text[start:end].splitlines()[1:] if line.strip()]


def test_jupyter_notebook_extra_targets_modern_widgets_by_default():
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")

    assert _extract_extra(pyproject, "notebook") == [
        "jupyter-client>7.4.9",
        "jupyter-server>2.5.0",
        "ipywidgets>=8.0.0",
    ]
    assert _extract_extra(pyproject, "labv4") == _extract_extra(pyproject, "notebook")
    assert _extract_extra(pyproject, "notebook-legacy") == [
        "jupyter-client<=7.4.9,>6.0.0",
        "jupyter-server<=2.5.0",
        "ipywidgets<8.0.0,>7.0.0",
    ]
