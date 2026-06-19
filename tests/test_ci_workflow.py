from pathlib import Path


def test_auto_ci_fails_on_pygwalker_deprecation_warnings():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "-W error::DeprecationWarning:pygwalker" in workflow


def test_auto_ci_runs_notebooks_through_pytest_nbmake():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/auto-ci.yml").read_text(encoding="utf-8")

    assert "python -m pytest --nbmake --nbmake-kernel=python *.ipynb" in workflow
    assert "jupyter nbconvert --execute" not in workflow
