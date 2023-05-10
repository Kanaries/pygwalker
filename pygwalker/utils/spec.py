from urllib import request
import json
import os

from pygwalker_utils.config import get_config
from .errors import InvalidConfigIdError, PrivacyError


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


def get_spec_json(spec: str) -> str:
    if not spec or _is_json(spec):
        return spec

    file_exist = os.path.exists(spec)
    if file_exist:
        return _get_sepc_from_local(spec)

    if get_config("privacy")[0] == "offline":
        raise PrivacyError("Due to privacy policy, you can't use this spec offline")

    if spec.startswith(("http:", "https:")):
        return _get_spec_from_url(spec)

    if len(spec) == 32:
        return _get_spec_from_server(spec)

    raise FileNotFoundError(f"Spec config file not found: {spec}")
