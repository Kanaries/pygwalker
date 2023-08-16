from typing import List, Dict, Any
from datetime import datetime
import io
import json

import requests

from .global_var import GlobalVarManager
from pygwalker.errors import CloudFunctionError


class PrivateSession(requests.Session):
    """A session with kanaries"""
    def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
        req = super().prepare_request(request)
        req.headers["kanaries-api-key"] = GlobalVarManager.kanaries_api_key
        return req

    def send(self, request: requests.Request, **kwargs) -> requests.Response:
        resp = super().send(request, **kwargs)
        if resp.status_code != 200:
            raise CloudFunctionError(f"Request failed: {resp.text}")
        resp_json = resp.json()
        if resp_json["success"] is False:
            raise CloudFunctionError(f"Request failed: {resp_json['message']}")
        return resp


session = PrivateSession()


def _upload_dataset_meta(name: str) -> Dict[str, Any]:
    url = f"{GlobalVarManager.kanaries_api_host}/dataset/upload"
    params = {
        "name": name,
        "fileName": name + ".csv",
        "isPublic": True,
        "desc": "",
        "meta": {
            "extractHeader": True,
            "encoding": "utf-8",
            "type": "TEXT_FILE",
            "separator": ",",
        }
    }
    resp = session.post(url, json=params, timeout=10)
    return resp.json()["data"]


def _upload_dataset_callback(dataset_id: str, fid_list: List[str]) -> Dict[str, Any]:
    url = f"{GlobalVarManager.kanaries_api_host}/dataset/callback"
    params = {
        "datasetId": dataset_id,
        "fidList": fid_list
    }
    resp = session.post(url, json=params, timeout=10)
    return resp.json()


def _create_chart(*, dataset_id: str, name: str, meta: str, workflow: List[Dict[str, Any]]) -> Dict[str, Any]:
    url = f"{GlobalVarManager.kanaries_api_host}/chart"
    params = {
        "datasetId": dataset_id,
        "meta": meta,
        "query": json.dumps({"datasetId": dataset_id, "workflow": workflow}),
        "config": "{}",
        "name": name,
        "desc": "",
        "isPublic": True,
        "chartType": "",
    }
    resp = session.post(url, json={"chart": params}, timeout=10)
    return resp.json()["data"]


def _upload_file_to_s3(url: str, content: io.BytesIO):
    requests.put(url, content.getvalue(), timeout=300)


def create_shared_chart(
    *,
    dataset_content: io.BytesIO,
    fid_list: List[str],
    meta: str,
) -> str:
    if not GlobalVarManager.kanaries_api_key:
        raise CloudFunctionError((
            "Please set kanaries_api_key first. "
            "If you are not kanaries user, please register it from `https://kanaries.net/home/access`. "
            "If you are kanaries user, please get your api key from `https://kanaries.net/app/u/MarilynMonroe`, go workspace detail page to get it."
        ))
    name = f"pygwalker_{datetime.now().strftime('%Y%m%d%H%M')}"
    dataset_info = _upload_dataset_meta(name)
    dataset_id = dataset_info["datasetId"]
    upload_url = dataset_info["uploadUrl"]
    _upload_file_to_s3(upload_url, dataset_content)
    _upload_dataset_callback(dataset_id, fid_list)
    chart_info = _create_chart(
        dataset_id=dataset_id,
        name=name,
        meta=meta,
        workflow={}
    )
    return chart_info["shareUrl"]
