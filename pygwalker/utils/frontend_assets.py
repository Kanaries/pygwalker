import os
import posixpath
from pathlib import Path

from pygwalker._constants import ROOT_DIR


def frontend_asset_path(*path_parts: str) -> str:
    return os.path.join(ROOT_DIR, "templates", "dist", *path_parts)


def frontend_asset_pathlib(*path_parts: str) -> Path:
    """Return the built frontend asset as a ``pathlib.Path``.

    Used by the anywidget dev/HMR path: when ``_esm`` is a ``Path`` (instead of the
    embedded source string) anywidget can read it from disk and, with
    ``ANYWIDGET_HMR=1``, watch it for changes and live-reload the widget.
    """
    path = Path(frontend_asset_path(*path_parts))
    if not path.exists():
        rel_path = posixpath.join("pygwalker", "templates", "dist", *path_parts)
        raise RuntimeError(
            f"Missing PyGWalker frontend asset: {rel_path}. "
            "Build the frontend first: run `python scripts/dev.py` (dev watch) "
            "or `cd app && yarn build` before enabling dev mode."
        )
    return path


def read_frontend_asset(*path_parts: str, encoding: str = "utf8") -> str:
    path = frontend_asset_path(*path_parts)
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except FileNotFoundError as exc:
        rel_path = posixpath.join("pygwalker", "templates", "dist", *path_parts)
        raise RuntimeError(
            f"Missing PyGWalker frontend asset: {rel_path}. "
            "Run `./scripts/compile.sh` from the repository root before using source-checkout builds."
        ) from exc
