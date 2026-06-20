"""Run the local equivalent of the GitHub Actions Auto CI workflow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
TESTS_DIR = REPO_ROOT / "tests"
PYTHON_TARGETS = ["pygwalker", "tests", "scripts", "bin", "pygwalker_tools"]


def run(command: list[str], cwd: Path = REPO_ROOT) -> None:
    print(f"\n$ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def run_frontend_ci() -> None:
    run(["sh", "scripts/compile.sh"])
    run(["yarn", "playwright", "install", "--with-deps", "chromium"], cwd=APP_DIR)
    run(["yarn", "test:front_end"], cwd=APP_DIR)


def run_notebook_ci() -> None:
    run([sys.executable, "scripts/test-init.py"])
    run([sys.executable, "-m", "pip", "install", "ipykernel", "nbmake", "pandas", "polars", "pytest"])
    run([sys.executable, "-m", "ipykernel", "install", "--name", "python", "--user"])
    run(["jupyter", "kernelspec", "list"])

    notebooks = sorted(path.name for path in TESTS_DIR.glob("*.ipynb"))
    run([sys.executable, "-m", "pytest", "--nbmake", "--nbmake-kernel=python", *notebooks], cwd=TESTS_DIR)


def install_legacy_modin_ci_deps() -> None:
    run([sys.executable, "-m", "pip", "install", "numpy<2", "pandas<2.1"])
    run([sys.executable, "-m", "pip", "install", "aiohttp==3.8.6"])
    run([sys.executable, "-m", "pip", "install", "modin==0.23.1", "modin[ray]==0.23.1"])
    run([sys.executable, "-m", "pip", "install", "pydantic==1.10.9"])


def run_python_ci() -> None:
    run([sys.executable, "-m", "pip", "install", "duckdb_engine"])
    run([sys.executable, "-m", "pip", "install", "pytest", "ruff", "starlette", "polars", "tornado"])
    run([sys.executable, "-m", "ruff", "check", *PYTHON_TARGETS])
    run([sys.executable, "-m", "ruff", "format", "--check", *PYTHON_TARGETS])
    run(
        [
            sys.executable,
            "-X",
            "faulthandler",
            "-W",
            "error::DeprecationWarning:pygwalker",
            "-m",
            "pytest",
            "-o",
            "faulthandler_timeout=300",
            "tests",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-frontend", action="store_true", help="Skip build-js equivalent checks.")
    parser.add_argument("--skip-notebooks", action="store_true", help="Skip nbmake notebook execution.")
    parser.add_argument("--legacy-modin-deps", action="store_true", help="Mirror the Ubuntu Python 3.11 modin CI leg.")
    args = parser.parse_args()

    if not args.skip_frontend:
        run_frontend_ci()
    if args.legacy_modin_deps:
        install_legacy_modin_ci_deps()
    if not args.skip_notebooks:
        run_notebook_ci()
    run_python_ci()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
