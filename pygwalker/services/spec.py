from urllib import request
from typing import Tuple, Dict, Any, List
from distutils.version import StrictVersion
import json
import os

from pygwalker_utils.config import get_config
from pygwalker.utils.randoms import rand_str
from pygwalker.services.fname_encodings import rename_columns
from pygwalker.errors import InvalidConfigIdError, PrivacyError
from .fname_encodings import fname_encode


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


def _config_adapter(config: str) -> str:
    config_obj = json.loads(config)
    for chart_item in config_obj:
        old_fid_fname_map = {
            field["fid"]: field["name"]
            for field in chart_item["encodings"]["dimensions"] + chart_item["encodings"]["measures"]
            if not field.get("computed", False)
        }
        new_fid_list = [fname_encode(fname) for fname in rename_columns(old_fid_fname_map.values())]
        old_new_fid_map = dict(zip(old_fid_fname_map.keys(), new_fid_list))

        for fields in chart_item["encodings"].values():
            for field in fields:
                if field.get("computed", False):
                    for param in field["expression"]["params"]:
                        if param["type"] == "field":
                            param["value"] = old_new_fid_map[param["value"]]
                else:
                    field["fid"] = old_new_fid_map[field["fid"]]
    return json.dumps(config_obj)


def fill_new_fields(config: str, all_fields: List[Dict[str, str]]) -> str:
    """when df schema changed, fill new fields to every chart config"""
    config_obj = json.loads(config)
    for chart_item in config_obj:
        field_set = {
            field["fid"]
            for field in chart_item["encodings"]["dimensions"] + chart_item["encodings"]["measures"]
        }
        new_dimension_fields = []
        new_measure_fields = []
        for field in all_fields:
            if field["fid"] not in field_set:
                gw_field = {
                    **field,
                    "basename": field["name"],
                    "dragId": "GW_" + rand_str()
                }
                if field["analyticType"] == "dimension":
                    new_dimension_fields.append(gw_field)
                else:
                    new_measure_fields.append(gw_field)

        chart_item["encodings"]["dimensions"].extend(new_dimension_fields)
        chart_item["encodings"]["measures"].extend(new_measure_fields)
    return json.dumps(config_obj)


def get_spec_json(spec: str) -> Tuple[Dict[str, Any], str]:
    spec, spec_type = _get_spec_json_from_diff_source(spec)

    if not spec:
        return {"chart_map": {}, "config": ""}, spec_type

    try:
        spec_obj = json.loads(spec)
    except json.decoder.JSONDecodeError as e:
        raise ValueError("spec is not a valid json") from e

    if isinstance(spec_obj, list):
        spec_obj = {"chart_map": {}, "config": spec}

    if StrictVersion(spec_obj.get("version", "0.1.0")) < StrictVersion("0.3.4"):
        spec_obj["config"] = _config_adapter(spec_obj["config"])

    return spec_obj, spec_type
