from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_auto_ci_fails_on_pygwalker_deprecation_warnings():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "-W error::DeprecationWarning:pygwalker" in workflow


def test_auto_ci_runs_pytest_directly_without_watchdog():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "scripts/ci_run_pytest.py" not in workflow
    assert not (REPO_ROOT / "scripts/ci_run_pytest.py").exists()


def test_auto_ci_runs_notebooks_through_pytest_nbmake():
    workflow = (REPO_ROOT / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "python -m pytest --nbmake --nbmake-kernel=python *.ipynb" in workflow
    assert "jupyter nbconvert --execute" not in workflow
