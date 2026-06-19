import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union

from pygwalker.services.spec import get_spec_json


SpecInput = Union[str, List[Any], Dict[str, Any]]


def _json_loads(value: str) -> Any:
    try:
        return json.loads(value)
    except ValueError as exc:
        raise ValueError("spec is not a valid json") from exc


def _is_json_string(value: str) -> bool:
    try:
        _json_loads(value)
    except ValueError:
        return False
    return True


def _load_spec_object(spec: SpecInput) -> Union[List[Any], Dict[str, Any]]:
    if isinstance(spec, str):
        if _is_json_string(spec):
            parsed_spec = _json_loads(spec)
        else:
            with open(spec, "r", encoding="utf-8") as f:
                parsed_spec = _json_loads(f.read())
    else:
        parsed_spec = spec

    if not isinstance(parsed_spec, (dict, list)):
        raise ValueError("spec must contain a JSON object or array")

    return parsed_spec


def migrate(spec: SpecInput, *, version: Optional[str] = None) -> Dict[str, Any]:
    """Migrate a saved PyGWalker or Graphic Walker spec to the current schema shape."""
    if isinstance(spec, str) and not _is_json_string(spec):
        if spec.lstrip().startswith(("{", "[")):
            raise ValueError("spec is not a valid json")
        if not os.path.exists(spec):
            raise ValueError("spec must be a dict, list, JSON string, or existing local file path")

    spec_obj = _load_spec_object(spec)
    migrated, _ = get_spec_json(deepcopy(spec_obj))
    if version is None:
        from pygwalker import __version__

        version = __version__
    migrated["version"] = version
    migrated.setdefault("chart_map", {})
    migrated.setdefault("workflow_list", [])
    return migrated
