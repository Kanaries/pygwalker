from pathlib import Path

from packaging.version import Version

import pygwalker


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


def _extract_sdist_force_include(pyproject_text: str) -> dict[str, str]:
    section_start = pyproject_text.index("[tool.hatch.build.targets.sdist.force-include]")
    section_end = pyproject_text.find("\n[", section_start + 1)
    if section_end == -1:
        section_end = len(pyproject_text)

    entries = {}
    for line in pyproject_text[section_start:section_end].splitlines()[1:]:
        if not line.strip():
            continue
        source, target = line.split("=", maxsplit=1)
        entries[source.strip().strip('"')] = target.strip().strip('"')
    return entries


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
    assert "pyarrow>=10,<25" in dependencies


def test_release_version_is_derived_from_package_init():
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    parsed_version = Version(pygwalker.__version__)

    assert 'dynamic = ["version"]' in pyproject
    assert 'version = { path = "pygwalker/__init__.py" }' in pyproject
    assert parsed_version.release == (0, 6, 0)


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
    assert "/pygwalker" in _extract_hatch_build_include(pyproject)


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
    assert "/pygwalker_tools" in _extract_hatch_build_include(pyproject)
    assert "/pygwalker_tools" in _extract_hatch_sdist_include(pyproject)


def test_hatch_build_includes_root_bin_only():
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    assert "/bin" in _extract_hatch_build_include(pyproject)
    assert "bin" not in _extract_hatch_build_include(pyproject)


def test_sdist_force_includes_frontend_lib_alias_sources():
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")

    assert (repo_root / "app/src/lib/utils.ts").is_file()
    assert _extract_sdist_force_include(pyproject)["app/src/lib"] == "app/src/lib"
