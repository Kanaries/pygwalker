from urllib import request
from typing import Tuple, Dict, Any, List, Union
from packaging.version import Version
from copy import deepcopy
import json
import os

from pygwalker.services.global_var import GlobalVarManager
from pygwalker.utils.randoms import rand_str
from pygwalker.services.fname_encodings import rename_columns
from pygwalker.services.cloud_service import read_config_from_cloud
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


def _get_spec_from_local(path: str) -> str:
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
    if not spec:
        return "", "empty_string"

    if _is_json(spec):
        return spec, "json_string"

    if spec.startswith("ksf://"):
        if GlobalVarManager.privacy == "offline":
            raise PrivacyError("Due to privacy policy, you can't use this spec offline")
        return read_config_from_cloud(spec[6:]), "json_ksf"

    if spec.startswith(("http:", "https:")):
        if GlobalVarManager.privacy == "offline":
            raise PrivacyError("Due to privacy policy, you can't use this spec offline")
        return _get_spec_from_url(spec), "json_http"

    if _is_config_id(spec):
        if GlobalVarManager.privacy == "offline":
            raise PrivacyError("Due to privacy policy, you can't use this spec offline")
        return _get_spec_from_server(spec), "json_server"

    if len(os.path.basename(spec)) > 200:
        raise ValueError("Spec file name too long")

    file_exist = os.path.exists(spec)
    if file_exist:
        return _get_spec_from_local(spec), "json_file"
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
            if not field.get("computed", False) and field.get("fid") not in ["gw_mea_val_fid", "gw_mea_key_fid"]
        }
        old_fid_list = []
        fname_list = []
        for old_fid, fname in old_fid_fname_map.items():
            old_fid_list.append(old_fid)
            fname_list.append(fname)

        new_fid_list = rename_columns(fname_list)
        for old_fid, new_fid in zip(old_fid_list, new_fid_list):
            config = config.replace(old_fid, new_fid)

    return config


def fill_new_fields(config: List[Dict[str, Any]], all_fields: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """when df schema changed, fill new fields to every chart config"""
    config = deepcopy(config)
    for chart_item in config:
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
    return config


def _config_adapter_045a5(config: List[Dict[str, Any]]):
    config = deepcopy(config)

    for chart_item in config:
        if "config" in chart_item and chart_item["config"].get("timezoneDisplayOffset", None) is None:
            chart_item["config"]["timezoneDisplayOffset"] = 0

        for item_list in chart_item["encodings"].values():
            for item in item_list:
                item["offset"] = 0
                if isinstance(item.get("expression", {}).get("params"), list):
                    for param in item["expression"]["params"]:
                        if param.get("type") == "offset":
                            param["value"] = 0

    return config


def _is_gw_config(config: Dict[str, Any]) -> bool:
    return not bool({"config", "encodings", "visId"} - set(config.keys()))


def _is_pygwalker_config(config: Dict[str, Any]) -> bool:
    return "config" in config and isinstance(config["config"], (list, str))


def get_spec_json(spec: Union[str, List[Any], Dict[str, Any]]) -> Tuple[Dict[str, Any], str]:
    if isinstance(spec, str):
        spec, spec_type = _get_spec_json_from_diff_source(spec)
        if not spec:
            return {"chart_map": {}, "config": [], "workflow_list": []}, spec_type

        try:
            spec_obj = json.loads(spec)
        except json.decoder.JSONDecodeError as e:
            raise ValueError("spec is not a valid json") from e
    else:
        spec_obj = spec
        spec_type = "json_obj"

    if isinstance(spec_obj, list):
        if spec_obj and not _is_gw_config(spec_obj[0]):
            return {"chart_map": {}, "config": spec_obj, "workflow_list": []}, "vega_list"
        else:
            spec_obj = {"chart_map": {}, "config": json.dumps(spec_obj), "workflow_list": []}

    if isinstance(spec_obj, dict) and not _is_pygwalker_config(spec_obj):
        return {"chart_map": {}, "config": [spec_obj], "workflow_list": []}, "vega_single"

    if Version(spec_obj.get("version", "0.1.0")) <= Version("0.3.17a4"):
        spec_obj["config"] = _config_adapter(spec_obj["config"])
    

    if isinstance(spec_obj["config"], str):
        spec_obj["config"] = json.loads(spec_obj["config"])

    if Version(spec_obj.get("version", "0.1.0")) <= Version("0.4.7a5"):
        spec_obj["config"] = _config_adapter_045a5(spec_obj["config"])

    return spec_obj, spec_type
