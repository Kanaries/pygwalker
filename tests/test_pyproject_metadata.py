from pathlib import Path


def _extract_extra(pyproject_text: str, extra_name: str) -> list[str]:
    start = pyproject_text.index(f"{extra_name} = [")
    end = pyproject_text.index("]", start)
    return [line.strip().strip('",') for line in pyproject_text[start:end].splitlines()[1:] if line.strip()]


def _extract_project_dependencies(pyproject_text: str) -> list[str]:
    start = pyproject_text.index("dependencies = [")
    end = pyproject_text.index("]", start)
    return [line.strip().strip('",') for line in pyproject_text[start:end].splitlines()[1:] if line.strip()]


def _extract_hatch_build_include(pyproject_text: str) -> list[str]:
    section_start = pyproject_text.index("[tool.hatch.build]")
    include_start = pyproject_text.index("include = [", section_start)
    include_end = pyproject_text.index("]", include_start)
    return [
        line.strip().strip('",') for line in pyproject_text[include_start:include_end].splitlines()[1:] if line.strip()
    ]


def _extract_hatch_sdist_include(pyproject_text: str) -> list[str]:
    section_start = pyproject_text.index("[tool.hatch.build.targets.sdist]")
    include_start = pyproject_text.index("include = [", section_start)
    include_end = pyproject_text.index("]", include_start)
    return [
        line.strip().strip('",') for line in pyproject_text[include_start:include_end].splitlines()[1:] if line.strip()
    ]


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


def test_project_metadata_declares_supported_python_and_bounded_dependencies():
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    dependencies = _extract_project_dependencies(pyproject)

    assert 'requires-python = ">=3.10"' in pyproject
    assert "requests>=2.31,<3" in dependencies
    assert "sqlalchemy>=1.4,<3" in dependencies
    assert "pydantic>=1.10,<3" in dependencies
    assert "duckdb>=0.10.4,<2.0.0" in dependencies


def test_dev_extra_contains_ci_quality_tools():
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")

    assert {"pytest", "ruff", "nbmake"}.issubset(_extract_extra(pyproject, "dev"))


def test_jupyter_builder_does_not_skip_existing_frontend_bundle():
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")

    assert "skip-if-exists" not in pyproject


def test_package_declares_pep561_typed_marker():
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    assert (repo_root / "pygwalker/py.typed").is_file()
    assert "pygwalker" in _extract_hatch_build_include(pyproject)


def test_public_dataframe_type_alias_includes_pyarrow_table():
    repo_root = Path(__file__).resolve().parents[1]
    typing_source = (repo_root / "pygwalker/_typing.py").read_text(encoding="utf-8")

    assert "import pyarrow as pa" in typing_source
    assert "dataframe_types.append(pa.Table)" in typing_source


def test_package_keeps_pygwalker_tools_metrics_namespace():
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    assert (repo_root / "pygwalker_tools/metrics").is_dir()
    assert (repo_root / "tests/test_metrics_tools.py").is_file()
    assert "pygwalker_tools" in _extract_hatch_build_include(pyproject)
    assert "pygwalker_tools" in _extract_hatch_sdist_include(pyproject)
