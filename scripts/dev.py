#!/usr/bin/env python
"""Start the PyGWalker local dev stack with one command and centralized logs.

This launches the two long-running processes a frontend/full-stack contributor needs and
streams their output both to your terminal and to per-service files under ``logs/``:

    * frontend  -> ``cd app && yarn dev:build`` (``vite build --watch``) rebuilds
      ``pygwalker/templates/dist/pygwalker-app.es.js`` every time you edit ``app/src``.
    * jupyter   -> ``jupyter lab`` with ``PYGWALKER_DEV=1`` / ``ANYWIDGET_HMR=1`` so the
      anywidget widget loads that bundle from disk and hot-reloads it live in the notebook.

With both running, editing ``app/src`` triggers a rebuild, and anywidget swaps the new code
into any open ``pyg.walk(df)`` widget without re-running the cell. See ``AGENTS.md`` and
``docs/DEVELOPMENT.md`` for the full workflow.

Examples
--------
    python scripts/dev.py                      # frontend watch + JupyterLab
    python scripts/dev.py --no-jupyter         # only rebuild the frontend on change
    python scripts/dev.py --no-frontend        # only JupyterLab (bundle already built)
    python scripts/dev.py --jupyter-port 8899 --no-browser
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
POSIX = os.name == "posix"

_shutting_down = threading.Event()


def _resolve_exe(name: str, hint: str) -> str:
    """Find an executable, preferring the one next to the current Python (venv)."""
    sibling = Path(sys.executable).parent / name
    if sibling.exists():
        return str(sibling)
    found = shutil.which(name)
    if found:
        return found
    sys.exit(f"error: `{name}` not found on PATH. {hint}")


class Service:
    """A managed child process that tees combined stdout/stderr to a log file."""

    def __init__(self, name: str, argv: list, cwd: Path, env: dict, log_path: Path):
        self.name = name
        self.argv = argv
        self.cwd = cwd
        self.env = env
        self.log_path = log_path
        self.proc: subprocess.Popen | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        # Truncate/create the log up front so a reader (e.g. _wait_for_first_build) can never
        # observe a previous run's output before the pump thread has opened the file.
        self.log_path.write_text("", encoding="utf-8")
        creationflags = 0
        if not POSIX:
            # Windows: give the child its own group so the whole tree can be signalled/killed.
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        self.proc = subprocess.Popen(
            self.argv,
            cwd=str(self.cwd),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=POSIX,  # POSIX: own process group -> clean group shutdown
            creationflags=creationflags,
        )
        self.thread = threading.Thread(target=self._pump, daemon=True)
        self.thread.start()

    def _pump(self) -> None:
        prefix = f"[{self.name}]"
        # Append: start() already truncated the file, so readers see only this run's output.
        with open(self.log_path, "a", encoding="utf-8", buffering=1) as log_file:
            assert self.proc is not None and self.proc.stdout is not None
            for line in self.proc.stdout:
                log_file.write(line)
                log_file.flush()
                sys.stdout.write(f"{prefix} {line}")
                sys.stdout.flush()

    def is_running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        if not POSIX:
            self._stop_windows()
            return
        try:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            return
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass

    def _stop_windows(self) -> None:
        # terminate() only kills the wrapper (e.g. yarn), leaving the node/Vite tree alive.
        # taskkill /T kills the whole process tree; fall back to terminate() if unavailable.
        assert self.proc is not None
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def _wait_for_first_build(service: "Service", timeout: float = 180.0) -> bool:
    """Block until `vite build --watch` reports a *finished* build.

    Returns True once a build completes, False if the frontend process exits first or the
    timeout elapses. Vite prints "watching for file changes" before the initial build
    finishes, so we key only on the "built in" completion marker.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not _shutting_down.is_set():
        try:
            text = service.log_path.read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            text = ""
        if "built in" in text:
            return True
        if not service.is_running():
            return False  # frontend exited before completing a build
        time.sleep(0.5)
    return False


def _build_env(log_dir: Path) -> dict:
    env = os.environ.copy()
    # Force the frontend dev path on: the widget loads the built ESM from disk and hot-reloads.
    env["PYGWALKER_DEV"] = "1"
    env["ANYWIDGET_HMR"] = "1"
    # Capture kernel-side pygwalker logs centrally (does not override an explicit choice).
    env.setdefault("PYGWALKER_LOG_FILE", str(log_dir / "pygwalker.log"))
    return env


def _install_signal_handlers() -> None:
    def _handler(signum, _frame):
        _shutting_down.set()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start the PyGWalker dev stack (frontend watch + JupyterLab) with central logs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--no-frontend", action="store_true", help="Do not run the frontend watch build.")
    parser.add_argument("--no-jupyter", action="store_true", help="Do not start JupyterLab.")
    parser.add_argument("--jupyter-port", type=int, default=None, help="Port for JupyterLab.")
    parser.add_argument(
        "--notebook-dir",
        default=str(REPO_ROOT),
        help="Working directory for JupyterLab (default: repo root).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a browser for JupyterLab (auto-enabled when output is not a TTY).",
    )
    parser.add_argument(
        "--log-dir",
        default=str(REPO_ROOT / "logs"),
        help="Directory for per-service log files (default: <repo>/logs).",
    )
    args = parser.parse_args()

    if args.no_frontend and args.no_jupyter:
        sys.exit("error: nothing to run (both --no-frontend and --no-jupyter given).")

    log_dir = Path(args.log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    env = _build_env(log_dir)

    services: list[Service] = []

    if not args.no_frontend:
        yarn = _resolve_exe("yarn", "Install Node.js 22.x and Yarn 1.x, then run `cd app && yarn install`.")
        services.append(Service("frontend", [yarn, "dev:build"], APP_DIR, env, log_dir / "frontend.log"))

    jupyter_service: Service | None = None
    if not args.no_jupyter:
        jupyter = _resolve_exe("jupyter", 'Install dev deps: `pip install -e ".[dev]"`.')
        jupyter_argv = [jupyter, "lab", f"--notebook-dir={args.notebook_dir}"]
        if args.no_browser or not sys.stdout.isatty():
            jupyter_argv.append("--no-browser")
        if args.jupyter_port is not None:
            jupyter_argv.append(f"--port={args.jupyter_port}")
        jupyter_service = Service("jupyter", jupyter_argv, REPO_ROOT, env, log_dir / "jupyter.log")

    _install_signal_handlers()

    print("=" * 78)
    print("PyGWalker dev stack")
    print(f"  logs directory : {log_dir}")
    if not args.no_frontend:
        print(f"  frontend       : yarn dev:build (vite build --watch)  -> {log_dir / 'frontend.log'}")
    if jupyter_service is not None:
        print(f"  jupyter lab    : PYGWALKER_DEV=1 ANYWIDGET_HMR=1        -> {log_dir / 'jupyter.log'}")
        print(f"  kernel logs    : PYGWALKER_LOG_FILE                     -> {env['PYGWALKER_LOG_FILE']}")
    print("=" * 78)

    # Start the frontend first and wait for its initial build so the kernel finds the bundle.
    frontend = next((svc for svc in services if svc.name == "frontend"), None)
    if frontend is not None:
        frontend.start()
        if jupyter_service is not None:
            print("[dev] waiting for the first frontend build to finish...")
            if _wait_for_first_build(frontend):
                print("[dev] frontend build ready.")
            elif not frontend.is_running():
                print("[dev] frontend build failed before completing; see logs/frontend.log.")
                print("[dev] not starting Jupyter.")
                _shutting_down.set()
            elif not _shutting_down.is_set():
                print("[dev] warning: timed out waiting for first build; starting Jupyter anyway.")

    if jupyter_service is not None and not _shutting_down.is_set():
        jupyter_service.start()
        services.append(jupyter_service)
        print("\n[dev] In a notebook cell, run your normal code — no special setup needed:")
        print("[dev]     import pandas as pd, pygwalker as pyg")
        print("[dev]     pyg.walk(pd.DataFrame({'x': [1, 2, 3]}))")
        print("[dev] Edit files under app/src/, watch logs/frontend.log rebuild, and the widget hot-reloads.")
        print("[dev] Find the JupyterLab URL/token in logs/jupyter.log. Press Ctrl+C to stop.\n")

    if not services:
        return 0

    try:
        while not _shutting_down.is_set():
            for svc in services:
                if not svc.is_running():
                    code = svc.proc.returncode if svc.proc else "?"
                    print(f"[dev] {svc.name} exited (code {code}); shutting down the rest.")
                    _shutting_down.set()
                    break
            time.sleep(0.5)
    finally:
        print("\n[dev] stopping services...")
        for svc in reversed(services):
            svc.stop()
        print("[dev] done.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
