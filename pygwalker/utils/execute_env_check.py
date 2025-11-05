import os
import re
from typing import List

try:
    import psutil
except Exception:  # pragma: no cover - platform dependent import
    psutil = None  # type: ignore[assignment]

from typing_extensions import Literal


def _get_parent_cmdline() -> List[str]:
    """Safely retrieve the parent process command line."""
    if psutil is None:
        return []

    try:
        parent = psutil.Process().parent()
    except Exception:
        return []

    if parent is None:
        return []

    try:
        return parent.cmdline()
    except Exception:
        return []


def check_convert() -> bool:
    """
    Check if the current process is a jupyter-nbconvert process.
    """
    for cmd in _get_parent_cmdline():
        if re.search(r"jupyter-nbconvert", cmd):
            return True
    return False


def check_kaggle() -> bool:
    """Check if the code is running on Kaggle."""
    return bool(os.environ.get("KAGGLE_KERNEL_RUN_TYPE"))


def get_kaggle_run_type() -> Literal["batch", "interactive"]:
    """Get the run type of Kaggle kernel."""
    return os.environ.get("KAGGLE_KERNEL_RUN_TYPE", "").lower()
