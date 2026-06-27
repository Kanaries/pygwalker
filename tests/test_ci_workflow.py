from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_auto_ci_fails_on_pygwalker_deprecation_warnings():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "-W error::DeprecationWarning:pygwalker" in workflow


def test_auto_ci_enforces_python_and_frontend_quality_gates():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "python-version: ['3.10', '3.11', '3.12', '3.13']" in workflow
    assert 'pip install "numpy<2" "pandas<2.1"' in workflow
    assert "ruff check pygwalker tests scripts bin pygwalker_tools" in workflow
    assert "ruff format --check pygwalker tests scripts bin pygwalker_tools" in workflow
    assert "pip install pytest ruff starlette polars tornado" in workflow
    assert "yarn playwright install --with-deps chromium" in workflow
    assert "yarn test:front_end" in workflow


def test_local_ci_script_mirrors_auto_ci_quality_gates():
    script = (REPO_ROOT / "scripts/local_ci.py").read_text(encoding="utf-8")

    assert '"scripts/compile.sh"' in script
    assert '"yarn", "playwright", "install", "--with-deps", "chromium"' in script
    assert '"yarn", "test:front_end"' in script
    assert '"numpy<2", "pandas<2.1"' in script
    assert '"pytest", "ruff", "starlette", "polars", "tornado"' in script
    assert '"--nbmake", "--nbmake-kernel=python"' in script
    assert '"ruff", "check", *PYTHON_TARGETS' in script
    assert '"ruff", "format", "--check", *PYTHON_TARGETS' in script
    assert '"error::DeprecationWarning:pygwalker"' in script
    assert '"faulthandler_timeout=300"' in script


def test_auto_ci_runs_pytest_directly_without_watchdog():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "scripts/ci_run_pytest.py" not in workflow
    assert not (REPO_ROOT / "scripts/ci_run_pytest.py").exists()


def test_auto_ci_runs_notebooks_through_pytest_nbmake():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "Path('.').glob('*.ipynb')" in workflow
    assert "python -m pytest --nbmake --nbmake-kernel=python *.ipynb" not in workflow
    assert "jupyter nbconvert --execute" not in workflow


def test_publish_workflow_packages_fresh_frontend_bundle():
    workflow = (REPO_ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")

    assert "node-version: [22.x]" in workflow
    assert "workflow_dispatch:" in workflow
    assert "./scripts/compile.sh" in workflow
    assert "name: pygwalker-app" in workflow
    assert "path: ./pygwalker/templates/dist/*" in workflow
    assert "build-py:\n    needs: [build-js]" in workflow
    assert "actions/download-artifact@v4" in workflow
    assert "path: ./pygwalker/templates/dist" in workflow
    assert "python -m build ." in workflow
    assert "pypa/gh-action-pypi-publish" in workflow

    build_py_start = workflow.index("  build-py:")
    download_dist_start = workflow.index("uses: actions/download-artifact@v4", build_py_start)
    build_package_start = workflow.index("python -m build .", build_py_start)
    assert download_dist_start < build_package_start
    assert "github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags')" in workflow
