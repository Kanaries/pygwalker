from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode
from typing_extensions import Literal
import logging
import io
import json
import hashlib

import requests

from .global_var import GlobalVarManager
from pygwalker.services.data_parsers import BaseDataParser
from pygwalker.errors import CloudFunctionError, ErrorCode

logger = logging.getLogger(__name__)


def _get_database_type_from_dialect_name(dialect_name: str) -> str:
    type_map = {
        "postgresql": "postgres",
    }
    type_name = type_map.get(dialect_name, dialect_name)
    return type_name[0].upper() + type_name[1:]


def _upload_file_to_s3(url: str, content: io.BytesIO):
    requests.put(url, content.getvalue(), timeout=300)


def _generate_chart_pre_redirect_uri(chart_id: str, auth_code_info: Dict[str, Any]) -> str:
    pre_uri = f"{GlobalVarManager.kanaries_main_host}/api/pygwalker/authCode"
    redirect_uri = f"{GlobalVarManager.kanaries_main_host}/share/pyg_chart/{chart_id}"

    params = {
        **auth_code_info,
        "successUrl": f"{redirect_uri}?mode=edit",
        "failUrl": f"{redirect_uri}?mode=view",
    }
    return pre_uri + "?" + urlencode(params)


def read_config_from_cloud(path: str) -> str:
    """Return config, if not exist, return empty string"""
    url = f"{GlobalVarManager.kanaries_api_host}/pygConfig"
    resp = requests.get(url, params={"path": path}, timeout=15)
    return resp.json()["data"]["config"]


class PrivateSession(requests.Session):
    """A session with kanaries"""
    def __init__(self, api_key: Optional[str]):
        super().__init__()
        self.kanaries_api_key = api_key

    def prepare_request(self, request: requests.Request) -> requests.PreparedRequest:
        req = super().prepare_request(request)
        req.headers["kanaries-api-key"] = self.kanaries_api_key
        return req

    def send(self, request: requests.PreparedRequest, **kwargs) -> requests.Response:
        kanaries_api_key = self.kanaries_api_key or GlobalVarManager.kanaries_api_key
        if not kanaries_api_key:
            logger.error((
                "kanaries_api_key is not valid.\n"
                "Please set kanaries_api_key first.\n"
                "If you are not kanaries user, please register it from 'https://kanaries.net/home/access' \n"
                "Then refer 'https://github.com/Kanaries/pygwalker/wiki/How-to-get-api-key-of-kanaries%3F' to set kanaries_api_key. \n"
            ))
            raise CloudFunctionError("no kanaries api key", code=ErrorCode.TOKEN_ERROR)
        resp = super().send(request, **kwargs)
        try:
            resp_json = resp.json()
        except Exception as e:
            raise CloudFunctionError(f"Request failed: {resp.text}") from e

        if "success" in resp_json:
            if resp_json["success"] is False:
                raise CloudFunctionError(
                    f"Request failed: {resp_json['message']}",
                    code=resp_json["code"] if resp_json["code"] != 0 else ErrorCode.UNKNOWN_ERROR
                )
        else:
            if resp.status_code != 200:
                raise CloudFunctionError(
                    f"Request failed: {resp_json['error']['message']}",
                    code=resp_json["error"]["code"]
                )

        return resp


class CloudService:
    """A class to manage cloud service"""
    def __init__(self, api_key: str):
        self.session = PrivateSession(api_key)

    def _upload_file_dataset_meta(
        self,
        name: str,
        file_type: str = Literal["parquet", "csv"],
        is_public: bool = True,
        kind: Literal["TEMP", "FILE"] = "FILE"
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
            },
            "type": kind,
        }
        resp = self.session.post(url, json=params, timeout=10)
        return resp.json()["data"]

    def _upload_dataset_callback(self, dataset_id: str, fid_list: List[str]) -> Dict[str, Any]:
        url = f"{GlobalVarManager.kanaries_api_host}/dataset/callback"
        params = {
            "datasetId": dataset_id,
            "fidList": fid_list
        }
        resp = self.session.post(url, json=params, timeout=10)
        return resp.json()

    def _create_chart(
        self,
        *,
        dataset_id: str,
        name: str,
        meta: str,
        workflow: List[Dict[str, Any]],
        thumbnail: str,
        is_public: bool,
    ) -> Dict[str, Any]:
        url = f"{GlobalVarManager.kanaries_api_host}/chart"
        params = {
            "datasetId": dataset_id,
            "meta": meta,
            "query": json.dumps({"datasetId": dataset_id, "workflow": workflow}),
            "config": "{}",
            "name": name,
            "desc": "",
            "isPublic": is_public,
            "chartType": "",
            "thumbnail": thumbnail,
        }
        resp = self.session.post(url, json={"chart": params}, timeout=10)
        return resp.json()["data"]

    def _create_notebook(self, title: str, chart_id: str) -> Dict[str, Any]:
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
        resp = self.session.post(url, json=params, timeout=10)
        return resp.json()["data"]

    def _get_chart_by_name(self, name: str, workspace_name: str) -> Optional[Dict[str, Any]]:
        url = f"{GlobalVarManager.kanaries_main_host}/api/pygwalker/chart"
        try:
            resp = self.session.get(url, params={"chartName": name, "workspaceName": workspace_name}, timeout=15)
        except CloudFunctionError as e:
            if e.code == ErrorCode.CLOUD_CHART_NOT_FOUND:
                return None
            raise e
        return resp.json()["data"]

    def _get_auth_code_info(self) -> Dict[str, Any]:
        url = f"{GlobalVarManager.kanaries_api_host}/auth/code"
        resp = self.session.get(url, timeout=15)
        return resp.json()["data"]

    def write_config_to_cloud(self, path: str, config: str):
        """Write config to cloud"""
        url = f"{GlobalVarManager.kanaries_api_host}/pygConfig"
        self.session.put(url, json={
            "path": path,
            "config": config
        })

    def get_cloud_graphic_walker(self, workspace_name: str, chart_name: str) -> str:
        chart_data = self._get_chart_by_name(chart_name, workspace_name)

        if chart_data is None:
            raise CloudFunctionError("chart not exists", code=ErrorCode.CLOUD_CHART_NOT_FOUND)

        try:
            auto_code_info = self._get_auth_code_info()
        except CloudFunctionError:
            auto_code_info = {}

        pre_redirect_uri = _generate_chart_pre_redirect_uri(chart_data["chartId"], auto_code_info)

        return pre_redirect_uri

    def create_cloud_graphic_walker(
        self,
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

        chart_data = self._get_chart_by_name(chart_name, workspace_name)

        if chart_data is not None:
            raise CloudFunctionError("chart name already exists", code=ErrorCode.UNKNOWN_ERROR)

        dataset_name = f"pygwalker_{datetime.now().strftime('%Y%m%d%H%M')}"
        dataset_info = self._upload_file_dataset_meta(dataset_name, "parquet")
        dataset_id = dataset_info["datasetId"]
        upload_url = dataset_info["uploadUrl"]
        _upload_file_to_s3(upload_url, dataset_content)
        self._upload_dataset_callback(dataset_id, fid_list)

        self._create_chart(
            dataset_id=dataset_id,
            name=chart_name,
            meta=meta,
            workflow={},
            thumbnail="",
            is_public=True
        )

    def get_kanaries_user_info(self) -> Dict[str, Any]:
        url = f"{GlobalVarManager.kanaries_api_host}/user/info"
        resp = self.session.get(url, timeout=15)
        return resp.json()["data"]

    def get_spec_by_text(self, metas: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        url = f"{GlobalVarManager.kanaries_api_host}/vis/text2gw"
        resp = self.session.post(
            url,
            json={"metas": metas, "messages": [{"role": "user", "content": text}]},
            timeout=15
        )
        return resp.json()["data"]

    def get_chart_by_chats(self, metas: List[Dict[str, Any]], chats: Any) -> Dict[str, Any]:
        url = f"{GlobalVarManager.kanaries_api_host}/vis/chat2gw"
        resp = self.session.post(
            url,
            json={"metas": metas, "messages": chats},
            timeout=30
        )
        return resp.json()["data"]

    def create_file_dataset(
        self,
        dataset_name: str,
        dataset_content: io.BytesIO,
        fid_list: List[str],
        is_public: bool,
        kind: Literal["TEMP", "FILE"]
    ) -> str:
        dataset_info = self._upload_file_dataset_meta(dataset_name, "parquet", is_public, kind=kind)
        dataset_id = dataset_info["datasetId"]
        upload_url = dataset_info["uploadUrl"]
        _upload_file_to_s3(upload_url, dataset_content)
        self._upload_dataset_callback(dataset_id, fid_list)
        return dataset_id

    def create_datasource(
        self,
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
        resp = self.session.post(url, json=params, timeout=15)
        return resp.json()["data"]["datasourceId"]

    def get_datasource_by_name(self, name: str) -> Optional[str]:
        url = f"{GlobalVarManager.kanaries_api_host}/datasource/search"
        resp = self.session.post(url, params={"fullName": name}, timeout=15)
        datasources = resp.json()["data"]["datasourceList"]
        return datasources[0]["id"] if datasources else None

    def create_database_dataset(
        self,
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
        resp = self.session.post(url, json=params, timeout=60)
        return resp.json()["data"]["datasetId"]

    def query_from_dataset(self, dataset_id: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = f"{GlobalVarManager.kanaries_api_host}/public/query"
        params = {
            "datasetId": dataset_id,
            "query": payload,
        }
        resp = self.session.post(url, json=params, timeout=15)
        return resp.json()["data"]

    def batch_query_from_dataset(self, dataset_id: str, query_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        url = f"{GlobalVarManager.kanaries_api_host}/v1/dataset/{dataset_id}/query"
        params = {
            "query": query_list,
        }
        resp = self.session.post(url, json=params, timeout=60)
        return resp.json()["data"]

    def create_cloud_dataset(
        self,
        data_parser: BaseDataParser,
        name: str,
        is_public: bool,
        is_temp_dataset: bool = False
    ) -> str:
        if name is None:
            name = f"pygwalker_{datetime.now().strftime('%Y%m%d%H%M')}"

        if data_parser.dataset_tpye == "cloud_dataset":
            raise ValueError("dataset is already a cloud dataset")

        if data_parser.dataset_tpye.startswith("connector"):
            connector = data_parser.conn
            datasource_name = "pygwalker_" + hashlib.md5(connector.url.encode()).hexdigest()
            datasource_id = self.get_datasource_by_name(datasource_name)
            if datasource_id is None:
                datasource_id = self.create_datasource(
                    datasource_name,
                    connector.url,
                    _get_database_type_from_dialect_name(connector.dialect_name)
                )
            dataset_id = self.create_database_dataset(
                name,
                datasource_id,
                is_public,
                connector.view_sql
            )
            return dataset_id
        else:
            dataset_id = self.create_file_dataset(
                name,
                data_parser.to_parquet(),
                [field["name"] for field in data_parser.raw_fields],
                is_public,
                kind="TEMP" if is_temp_dataset else "FILE"
            )

        return dataset_id

    def create_dashboard(
        self,
        *,
        name: str,
        layout: List[Any],
        config: Dict[str, Any],
        is_public: bool
    ) -> str:
        url = f"{GlobalVarManager.kanaries_api_host}/report"
        params = {
            "title": name,
            "version": "0.0.1",
            "desc": "",
            "size": {},
            "config": config,
            "layout": layout,
            "public": is_public
        }
        resp = self.session.post(url, json=params, timeout=60)
        return resp.json()["data"]["id"]

    def upload_cloud_chart(
        self,
        *,
        chart_name: str,
        dataset_name: str,
        data_parser: BaseDataParser,
        workflow: List[Dict[str, Any]],
        spec_list: List[Dict[str, Any]],
        is_public: bool,
    ) -> str:
        workspace_name = self.get_kanaries_user_info()["workspaceName"]

        chart_data = self._get_chart_by_name(chart_name, workspace_name)

        if chart_data is not None:
            raise CloudFunctionError("chart name already exists", code=ErrorCode.UNKNOWN_ERROR)

        dataset_id = self.create_cloud_dataset(data_parser, dataset_name, False)
        chart_info = self._create_chart(
            dataset_id=dataset_id,
            name=chart_name,
            meta=json.dumps({
                "dataSources": [{
                    "id": "dataSource-0",
                    "data": []
                }],
                "datasets": [{
                    "id": 'dataset-0',
                    "name": 'DataSet',
                    "rawFields": data_parser.raw_fields,
                    "dsId": 'dataSource-0',
                }],
                "specList": spec_list
            }),
            workflow=workflow,
            thumbnail="",
            is_public=is_public
        )

        return {
            "chart_id": chart_info["chartId"],
            "dataset_id": dataset_id
        }

    def upload_cloud_dashboard(
        self,
        *,
        dashboard_name: str,
        dataset_name: str,
        data_parser: BaseDataParser,
        workflow_list: List[List[Dict[str, Any]]],
        spec_list: List[Dict[str, Any]],
        is_public: bool,
        appearance: str,
        create_dashboard_flag: bool
    ) -> Dict[str, str]:
        dataset_id = self.create_cloud_dataset(data_parser, dataset_name, False)

        chart_info_list = []
        for spec, workflow in zip(spec_list, workflow_list):    
            chart_info = self._create_chart(
                dataset_id=dataset_id,
                name=f"{dashboard_name}-{spec['name']}",
                meta=json.dumps({
                    "dataSources": [{
                        "id": "dataSource-0",
                        "data": []
                    }],
                    "datasets": [{
                        "id": 'dataset-0',
                        "name": 'DataSet',
                        "rawFields": data_parser.raw_fields,
                        "dsId": 'dataSource-0',
                    }],
                    "specList": [spec]
                }),
                workflow=workflow,
                thumbnail="",
                is_public=is_public
            )

            chart_info_list.append(chart_info)

        if not create_dashboard_flag:
            return {
                "dashboard_id": "",
                "dataset_id": dataset_id
            }

        dashboard_id = self.create_dashboard(
            name=dashboard_name,
            is_public=is_public,
            config={
                "items": [
                    {"id": "dashboard_title", "content": f"# {dashboard_name}", "type": "text", "name": "Text"},
                    {
                        "id": "chart_tab",
                        "dark": appearance,
                        "name": "Charts",
                        "type": "data",
                        "tabs": [
                            {"chartId": chart_info["chartId"], "title": spec["name"]}
                            for spec, chart_info in zip(spec_list, chart_info_list)
                        ],
                        "mode": "gwtabs",
                    }
                ],
            },
            layout=[
                {"i": "dashboard_title", "h": 2, "w": 4, "x": 0, "y": 0},
                {"i": "chart_tab", "h": 20, "w": 4, "x": 0, "y": 2},
            ]
        )

        return {
            "dashboard_id": dashboard_id,
            "dataset_id": dataset_id
        }
