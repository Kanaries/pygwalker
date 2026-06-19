from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_auto_ci_fails_on_pygwalker_deprecation_warnings():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "-W error::DeprecationWarning:pygwalker" in workflow


def test_auto_ci_enforces_python_and_frontend_quality_gates():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "python-version: ['3.10', '3.11', '3.12', '3.13']" in workflow
    assert "ruff check pygwalker tests scripts bin pygwalker_tools" in workflow
    assert "ruff format --check pygwalker tests scripts bin pygwalker_tools" in workflow
    assert "yarn playwright install --with-deps chromium" in workflow
    assert "yarn test:front_end" in workflow


def test_auto_ci_runs_pytest_directly_without_watchdog():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "scripts/ci_run_pytest.py" not in workflow
    assert not (REPO_ROOT / "scripts/ci_run_pytest.py").exists()


def test_auto_ci_runs_notebooks_through_pytest_nbmake():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "python -m pytest --nbmake --nbmake-kernel=python *.ipynb" in workflow
    assert "jupyter nbconvert --execute" not in workflow
