import psutil
import re
import os

from typing_extensions import Literal


def check_convert() -> bool:
    """
    Check if the current process is a jupyter-nbconvert process.
    """
    if psutil.Process().parent() is None:
        return False
    cmd_list = psutil.Process().parent().cmdline()
    for cmd in cmd_list:
        if re.search(r"jupyter-nbconvert", cmd):
            return True
    return False


def check_kaggle() -> bool:
    """Check if the code is running on Kaggle."""
    return bool(os.environ.get("KAGGLE_KERNEL_RUN_TYPE"))


def get_kaggle_run_type() -> Literal["batch", "interactive"]:
    """Get the run type of Kaggle kernel."""
    return os.environ.get("KAGGLE_KERNEL_RUN_TYPE", "").lower()
