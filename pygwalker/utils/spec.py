import os
from typing import Any, Optional


def resolve_spec_input(spec: Any, spec_path: Optional[os.PathLike[str] | str]) -> Any:
    """Resolve explicit spec_path while keeping legacy spec behavior."""
    if spec_path is None:
        return spec

    if spec not in ("", None):
        raise ValueError("Pass only one of `spec` or `spec_path`; use `spec_path` for local spec files.")

    return os.fspath(spec_path)
