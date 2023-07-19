from urllib import request
from typing import Tuple, Dict, Any
import json
import os

from pygwalker_utils.config import get_config
from pygwalker.errors import InvalidConfigIdError, PrivacyError


def _is_json(s: str) -> bool:
    try:
        json.loads(s)
    except ValueError:
        return False
    return True


def _get_spec_from_server(config_id: str) -> str:
    url = f"https://i4rwxmw117.execute-api.us-east-1.amazonaws.com/default/pygwalker-config?config_id={config_id}"
    with request.urlopen(url, timeout=30) as resp:
        json_data = json.loads(resp.read().decode("utf-8"))

    if json_data["code"] != 0:
        raise InvalidConfigIdError(f"Invalid config id: {config_id}")

    return json_data["data"]["config_json"]


def _get_spec_from_url(url: str) -> str:
    with request.urlopen(url, timeout=15) as resp:
        return resp.read().decode("utf-8")


def _get_sepc_from_local(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _is_config_id(config_id: str) -> bool:
    if len(config_id) != 32:
        return False
    try:
        int(config_id, 16)
    except ValueError:
        return False

    return True


def _get_spec_json_from_diff_source(spec: str) -> Tuple[str, str]:
    if not spec or _is_json(spec):
        return spec, "json_string"

    if spec.startswith(("http:", "https:")):
        if get_config("privacy")[0] == "offline":
            raise PrivacyError("Due to privacy policy, you can't use this spec offline")
        return _get_spec_from_url(spec), "json_http"

    if _is_config_id(spec):
        if get_config("privacy")[0] == "offline":
            raise PrivacyError("Due to privacy policy, you can't use this spec offline")
        return _get_spec_from_server(spec), "json_server"

    if len(os.path.basename(spec)) > 200:
        raise ValueError("Spec file name too long")

    file_exist = os.path.exists(spec)
    if file_exist:
        return _get_sepc_from_local(spec), "json_file"
    else:
        with open(spec, "w", encoding="utf-8") as f:
            f.write("")
        return "", "json_file"


def get_spec_json(spec: str) -> Tuple[Dict[str, Any], str]:
    spec, spec_type = _get_spec_json_from_diff_source(spec)

    if not spec:
        return {"chart_map": {}, "config": ""}, spec_type

    try:
        spec_obj = json.loads(spec)
    except json.decoder.JSONDecodeError as e:
        raise ValueError("spec is not a valid json") from e

    if isinstance(spec_obj, list):
        return {"chart_map": {}, "config": spec}, spec_type

    return spec_obj, spec_type
