import os

from pygwalker._constants import ROOT_DIR


def frontend_asset_path(*path_parts: str) -> str:
    return os.path.join(ROOT_DIR, "templates", "dist", *path_parts)


def read_frontend_asset(*path_parts: str, encoding: str = "utf8") -> str:
    path = frontend_asset_path(*path_parts)
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except FileNotFoundError as exc:
        rel_path = os.path.join("pygwalker", "templates", "dist", *path_parts)
        raise RuntimeError(
            f"Missing PyGWalker frontend asset: {rel_path}. "
            "Run `./scripts/compile.sh` from the repository root before using source-checkout builds."
        ) from exc
