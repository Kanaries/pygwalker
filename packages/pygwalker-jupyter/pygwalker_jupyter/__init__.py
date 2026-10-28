"""Python package metadata for the PyGWalker prebuilt JupyterLab extension."""

from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("pygwalker-jupyter")
except PackageNotFoundError:  # Source checkout before installation.
    __version__ = "0.1.0.dev0"


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "@kanaries/pygwalker-jupyter"}]


__all__ = ["__version__", "_jupyter_labextension_paths"]
