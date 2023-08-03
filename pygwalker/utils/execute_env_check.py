import psutil
import re


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
