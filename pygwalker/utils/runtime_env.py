from typing_extensions import Literal


def _is_jupyter() -> bool:
    try:
        from IPython import get_ipython
        ip = get_ipython()
        if ip is None:
            return False
        return ip.has_trait('kernel')
    except Exception:
        return False


def get_current_env() -> Literal["jupyter", "other"]:
    """
    Get the current environment.

    Returns:
        Literal["jupyter", "other"]: The current environment.
    """
    if _is_jupyter():
        return "jupyter"
    else:
        return "other"
