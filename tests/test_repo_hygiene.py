import subprocess
from pathlib import Path

import pytest


FORBIDDEN_TRACKED_PATH_PARTS = (
    "__pycache__/",
    ".pytest_cache/",
    ".ipynb_checkpoints/",
    "pygwalker/templates/dist/",
)
FORBIDDEN_TRACKED_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".DS_Store",
    ".whl",
)


def _tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        pytest.skip("repo hygiene check requires a git checkout")
    return result.stdout.splitlines()


def test_generated_cache_and_package_artifacts_are_not_tracked():
    repo_root = Path(__file__).resolve().parents[1]

    forbidden_files = [
        path
        for path in _tracked_files(repo_root)
        if any(part in path for part in FORBIDDEN_TRACKED_PATH_PARTS)
        or any(path.endswith(suffix) for suffix in FORBIDDEN_TRACKED_SUFFIXES)
        or (path.startswith("dist/") and not path.endswith(".gitkeep"))
    ]

    assert forbidden_files == []
