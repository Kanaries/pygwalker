from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode
from typing_extensions import Literal
import io
import json

import requests

from .global_var import GlobalVarManager
from pygwalker.errors import CloudFunctionError, ErrorCode


class PrivateSession(requests.Session):
    """A session with kanaries"""
    def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
        req = super().prepare_request(request)
        req.headers["kanaries-api-key"] = GlobalVarManager.kanaries_api_key
        return req

    def send(self, request: requests.PreparedRequest, **kwargs) -> requests.Response:
        if not GlobalVarManager.kanaries_api_key and request.headers.get("__need_kanaries_api_key", "true") == "true":
            raise CloudFunctionError("no kanaries api key", code=ErrorCode.TOKEN_ERROR)
        request.headers.pop("__need_kanaries_api_key", None)
        resp = super().send(request, **kwargs)
        try:
            resp_json = resp.json()
        except Exception as e:
            raise CloudFunctionError(f"Request failed: {resp.text}") from e
        if resp_json["success"] is False:
            raise CloudFunctionError(f"Request failed: {resp_json['message']}", code=resp_json["code"])
        return resp


session = PrivateSession()


def _upload_file_dataset_meta(
    name: str,
    file_type: str = Literal["parquet", "csv"],
    is_public: bool = True
) -> Dict[str, Any]:
    param_file_type_map = {
        "csv": "TEXT_FILE",
        "parquet": "PARQUET"
    }

    url = f"{GlobalVarManager.kanaries_api_host}/dataset/upload"
    params = {
        "name": name,
        "fileName": name + "." + file_type,
        "isPublic": is_public,
        "desc": "",
        "meta": {
            "extractHeader": True,
            "encoding": "utf-8",
            "type": param_file_type_map.get(file_type, "TEXT_FILE"),
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


def _create_chart(
    *,
    dataset_id: str,
    name: str,
    meta: str,
    workflow: List[Dict[str, Any]],
    thumbnail: str
) -> Dict[str, Any]:
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
        "thumbnail": thumbnail,
    }
    resp = session.post(url, json={"chart": params}, timeout=10)
    return resp.json()["data"]


def _create_notebook(title: str, chart_id: str) -> Dict[str, Any]:
    url = f"{GlobalVarManager.kanaries_api_host}/notebook"
    markdown = "\n".join([
        "# " + title,
        f"::chart[{chart_id}]"
    ])
    params = {
        "title": title,
        "markdown": markdown,
        "isPublic": True,
    }
    resp = session.post(url, json=params, timeout=10)
    return resp.json()["data"]


def _upload_file_to_s3(url: str, content: io.BytesIO):
    requests.put(url, content.getvalue(), timeout=300)


def _get_chart_by_name(name: str, workspace_name: str) -> Optional[Dict[str, Any]]:
    url = f"{GlobalVarManager.kanaries_main_host}/api/pygwalker/chart"
    try:
        resp = session.get(url, params={"chartName": name, "workspaceName": workspace_name}, timeout=15)
    except CloudFunctionError as e:
        if e.code == ErrorCode.CLOUD_CHART_NOT_FOUND:
            return None
        raise e
    return resp.json()["data"]


def _get_auth_code_info() -> Dict[str, Any]:
    url = f"{GlobalVarManager.kanaries_api_host}/auth/code"
    resp = session.get(url, timeout=15)
    return resp.json()["data"]


def _generate_chart_pre_redirect_uri(chart_id: str, auth_code_info: Dict[str, Any]) -> str:
    pre_uri = f"{GlobalVarManager.kanaries_main_host}/api/pygwalker/authCode"
    redirect_uri = f"{GlobalVarManager.kanaries_main_host}/share/pyg_chart/{chart_id}"

    params = {
        **auth_code_info,
        "successUrl": f"{redirect_uri}?mode=edit",
        "failUrl": f"{redirect_uri}?mode=view",
    }
    return pre_uri + "?" + urlencode(params)


def write_config_to_cloud(path: str, config: str):
    """Write config to cloud"""
    url = f"{GlobalVarManager.kanaries_api_host}/pygConfig"
    session.put(url, json={
        "path": path,
        "config": config
    })


def read_config_from_cloud(path: str) -> str:
    """Return config, if not exist, return empty string"""
    url = f"{GlobalVarManager.kanaries_api_host}/pygConfig"
    resp = session.get(url, params={"path": path}, headers={"__need_kanaries_api_key": "false"}, timeout=15)
    return resp.json()["data"]["config"]


def get_cloud_graphic_walker(workspace_name: str, chart_name: str) -> str:
    chart_data = _get_chart_by_name(chart_name, workspace_name)

    if chart_data is None:
        raise CloudFunctionError("chart not exists", code=ErrorCode.CLOUD_CHART_NOT_FOUND)

    try:
        auto_code_info = _get_auth_code_info()
    except CloudFunctionError:
        auto_code_info = {}

    pre_redirect_uri = _generate_chart_pre_redirect_uri(chart_data["chartId"], auto_code_info)

    return pre_redirect_uri


def create_cloud_graphic_walker(
    *,
    chart_name: str,
    workspace_name: str,
    dataset_content: io.BytesIO,
    field_specs: List[Dict[str, Any]],
) -> str:
    fid_list = [field["fid"] for field in field_specs]
    meta = json.dumps({
        "dataSources": [{
            "id": "dataSource-0",
            "data": []
        }],
        "datasets": [{
            "id": 'dataset-0',
            "name": 'DataSet',
            "rawFields": field_specs,
            "dsId": 'dataSource-0',
        }],
        "specList": []
    })

    chart_data = _get_chart_by_name(chart_name, workspace_name)

    if chart_data is not None:
        raise CloudFunctionError("chart name already exists", code=ErrorCode.UNKNOWN_ERROR)

    dataset_name = f"pygwalker_{datetime.now().strftime('%Y%m%d%H%M')}"
    dataset_info = _upload_file_dataset_meta(dataset_name, "parquet")
    dataset_id = dataset_info["datasetId"]
    upload_url = dataset_info["uploadUrl"]
    _upload_file_to_s3(upload_url, dataset_content)
    _upload_dataset_callback(dataset_id, fid_list)

    _create_chart(
        dataset_id=dataset_id,
        name=chart_name,
        meta=meta,
        workflow={},
        thumbnail="",
    )


def get_kanaries_user_info() -> Dict[str, Any]:
    url = f"{GlobalVarManager.kanaries_api_host}/user/info"
    resp = session.get(url, timeout=15)
    return resp.json()["data"]


def get_spec_by_text(metas: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
    url = f"{GlobalVarManager.kanaries_api_host}/vis/text2gw"
    resp = session.post(
        url,
        json={"metas": metas, "messages": [{"role": "user", "content": text}]},
        timeout=15
    )
    return resp.json()["data"]


def create_file_dataset(
    dataset_name: str,
    dataset_content: io.BytesIO,
    fid_list: List[str],
    is_public: bool,
) -> str:
    dataset_info = _upload_file_dataset_meta(dataset_name, "parquet", is_public)
    dataset_id = dataset_info["datasetId"]
    upload_url = dataset_info["uploadUrl"]
    _upload_file_to_s3(upload_url, dataset_content)
    _upload_dataset_callback(dataset_id, fid_list)
    return dataset_id


def create_datasource(
    name: str,
    database_url: str,
    database_type: str,
) -> str:
    url = f"{GlobalVarManager.kanaries_api_host}/datasource"
    params = {
        "name": name,
        "connectionconfiguration": {
            "url": database_url,
        },
        "datasourceType": database_type,
        "desc": ""
    }
    resp = session.post(url, json=params, timeout=15)
    return resp.json()["data"]["datasourceId"]


def get_datasource_by_name(name: str) -> Optional[str]:
    url = f"{GlobalVarManager.kanaries_api_host}/datasource/search"
    resp = session.post(url, params={"fullName": name}, timeout=15)
    datasources = resp.json()["data"]["datasourceList"]
    return datasources[0]["id"] if datasources else None


def create_database_dataset(
    name: str,
    datasource_id: str,
    is_public: bool,
    view_sql: str,
) -> str:
    url = f"{GlobalVarManager.kanaries_api_host}/dataset"
    params = {
        "name": name,
        "desc": "",
        "datasourceId": datasource_id,
        "isPublic": is_public,
        "type": "DATABASE",
        "meta": {
            "viewSql": view_sql,
        }
    }
    resp = session.post(url, json=params, timeout=60)
    return resp.json()["data"]["datasetId"]


def query_from_dataset(dataset_id: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = f"{GlobalVarManager.kanaries_api_host}/public/query"
    params = {
        "datasetId": dataset_id,
        "query": payload,
    }
    resp = session.post(url, json=params, timeout=15)
    return resp.json()["data"]
