import base64
import json
import os
import subprocess
import sys
import urllib.parse
import zlib
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

import pandas as pd

from pygwalker import __version__
from pygwalker.communications.base import BaseCommunication
from pygwalker.communications.protocol import (
    AskSpecRequest,
    BatchPayloadQueryRequest,
    BatchSqlQueryRequest,
    ChatChartRequest,
    OpenDesktopRequest,
    PayloadQueryRequest,
    SaveChartRequest,
    SqlQueryRequest,
    UploadCloudChartRequest,
    UploadCloudDashboardRequest,
    UpdateSpecRequest,
    UploadSpecToCloudRequest,
    validate_request,
)
from pygwalker.services.config import set_config
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.preview_image import PreviewImageTool
from pygwalker.services.upload_data import BatchUploadDatasToolOnWidgets
from pygwalker.utils.pydantic_compat import model_dump

if TYPE_CHECKING:
    from pygwalker.api.pygwalker import PygWalker


class CommHandler:
    """Register and serve frontend communication callbacks for a walker."""

    def __init__(
        self,
        walker: "PygWalker",
        comm: BaseCommunication,
        preview_tool: Optional[PreviewImageTool] = None,
        upload_tool_cls: Callable[[BaseCommunication], BatchUploadDatasToolOnWidgets] = BatchUploadDatasToolOnWidgets,
    ):
        self.walker = walker
        self.comm = comm
        self.preview_tool = preview_tool
        self.upload_tool = upload_tool_cls(comm)

    def register(self) -> None:
        self.walker.comm = self.comm

        self.comm.register("get_latest_vis_spec", self.get_latest_vis_spec)
        self.comm.register("request_data", self.request_data)
        self.comm.register("ping", lambda _: {})
        self.comm.register("open_in_desktop", self.open_in_desktop)

        if self.walker.use_save_tool:
            self.comm.register("upload_spec_to_cloud", self.upload_spec_to_cloud)
            self.comm.register("update_spec", self.update_spec)
            self.comm.register("save_chart", self.save_chart)

        if self.walker.show_cloud_tool:
            self.comm.register("upload_to_cloud_charts", self.upload_to_cloud_charts)
            self.comm.register("upload_to_cloud_dashboard", self.upload_to_cloud_dashboard)
            self.comm.register("get_spec_by_text", self.get_spec_by_text)
            self.comm.register("get_chart_by_chats", self.get_chart_by_chats)

        if self.walker.kernel_computation:
            self.comm.register("get_datas", self.get_datas)
            self.comm.register("get_datas_by_payload", self.get_datas_by_payload)
            self.comm.register("batch_get_datas_by_sql", self.batch_get_datas_by_sql)
            self.comm.register("batch_get_datas_by_payload", self.batch_get_datas_by_payload)

        if self.walker.is_export_dataframe:
            self.comm.register("export_dataframe_by_payload", self.export_dataframe_by_payload)
            self.comm.register("export_dataframe_by_sql", self.export_dataframe_by_sql)

    def request_data(self, _):
        self.upload_tool.run(
            records=self.walker.origin_data_source,
            sample_data_count=0,
            data_source_id=self.walker.data_source_id,
        )
        return {}

    def get_latest_vis_spec(self, _):
        return {"visSpec": self.walker.vis_spec}

    def save_chart(self, data: Dict[str, Any]):
        request = validate_request(SaveChartRequest, data)
        self.walker.spec_manager.save_chart_payload(model_dump(request, by_alias=True))

    def update_spec(self, data: Dict[str, Any]):
        request = validate_request(UpdateSpecRequest, data)
        self.walker.spec_manager.update_runtime_state(
            vis_spec=request.vis_spec,
            workflow_list=request.workflow_list,
            chart_data=request.chart_data,
            version=__version__,
        )

        if self.walker.use_preview:
            self.preview_tool.async_render_gw_review(self.walker._get_gw_preview_html())

        self.walker.spec_manager.write_back(self.walker.cloud_service, __version__)

    def upload_spec_to_cloud(self, data: Dict[str, Any]):
        request = validate_request(UploadSpecToCloudRequest, data)
        if request.new_token:
            set_config({"kanaries_token": request.new_token})
            GlobalVarManager.kanaries_api_key = request.new_token
        spec_obj = self.walker.spec_manager.build_spec_obj(__version__)
        workspace_name = self.walker.cloud_service.get_kanaries_user_info()["workspaceName"]
        path = f"{workspace_name}/{request.file_name}"
        self.walker.cloud_service.write_config_to_cloud(path, json.dumps(spec_obj))
        return {"specFilePath": path}

    def get_datas(self, data: Dict[str, Any]):
        request = validate_request(SqlQueryRequest, data)
        datas = self.walker.data_parser.get_datas_by_sql(request.sql)
        return {"datas": datas}

    def get_datas_by_payload(self, data: Dict[str, Any]):
        request = validate_request(PayloadQueryRequest, data)
        datas = self.walker.data_parser.get_datas_by_payload(model_dump(request.payload, exclude_none=True))
        return {"datas": datas}

    def batch_get_datas_by_sql(self, data: Dict[str, Any]):
        request = validate_request(BatchSqlQueryRequest, data)
        result = self.walker.data_parser.batch_get_datas_by_sql(request.query_list)
        return {"datas": result}

    def batch_get_datas_by_payload(self, data: Dict[str, Any]):
        request = validate_request(BatchPayloadQueryRequest, data)
        result = self.walker.data_parser.batch_get_datas_by_payload(
            [model_dump(query, exclude_none=True) for query in request.query_list]
        )
        return {"datas": result}

    def get_spec_by_text(self, data: Dict[str, Any]):
        request = validate_request(AskSpecRequest, data)
        callback = self.walker.other_props.get("custom_ask_callback", self.walker.cloud_service.get_spec_by_text)
        return {"data": callback(request.metas, request.query)}

    def get_chart_by_chats(self, data: Dict[str, Any]):
        request = validate_request(ChatChartRequest, data)
        callback = self.walker.other_props.get("custom_chat_callback", self.walker.cloud_service.get_chart_by_chats)
        return {"data": callback(request.metas, request.chats)}

    def export_dataframe_by_payload(self, data: Dict[str, Any]):
        request = validate_request(PayloadQueryRequest, data)
        df = pd.DataFrame(self.walker.data_parser.get_datas_by_payload(model_dump(request.payload, exclude_none=True)))
        GlobalVarManager.set_last_exported_dataframe(df)
        self.walker._last_exported_dataframe = df

    def export_dataframe_by_sql(self, data: Dict[str, Any]):
        request = validate_request(SqlQueryRequest, data)
        df = pd.DataFrame(self.walker.data_parser.get_datas_by_sql(request.sql))
        GlobalVarManager.set_last_exported_dataframe(df)
        self.walker._last_exported_dataframe = df

    def upload_to_cloud_charts(self, data: Dict[str, Any]):
        request = validate_request(UploadCloudChartRequest, data)
        result = self.walker.cloud_service.upload_cloud_chart(
            data_parser=self.walker.data_parser,
            chart_name=request.chart_name,
            dataset_name=request.dataset_name,
            workflow=request.workflow,
            spec_list=request.vis_spec,
            is_public=request.is_public,
        )
        return {"chartId": result["chart_id"], "datasetId": result["dataset_id"]}

    def upload_to_cloud_dashboard(self, data: Dict[str, Any]):
        request = validate_request(UploadCloudDashboardRequest, data)
        result = self.walker.cloud_service.upload_cloud_dashboard(
            data_parser=self.walker.data_parser,
            dashboard_name=request.chart_name,
            dataset_name=request.dataset_name,
            workflow_list=request.workflow_list,
            spec_list=request.vis_spec,
            is_public=request.is_public,
            create_dashboard_flag=request.is_create_dashboard,
            appearance=self.walker.appearance,
        )
        return {"dashboardId": result["dashboard_id"], "datasetId": result["dataset_id"]}

    def open_in_desktop(self, data: Dict[str, Any]):
        request = validate_request(OpenDesktopRequest, data)
        spec = json.dumps(request.spec)
        fields = json.dumps(request.fields)
        records = json.dumps(
            self.walker.data_parser.to_records(),
            default=lambda obj: obj.isoformat() if hasattr(obj, "isoformat") else str(obj),
        )
        self._open_protocol(
            f"gw://import?data={self._compress_data(records)}&spec={self._compress_data(spec)}&fields={self._compress_data(fields)}"
        )

    @staticmethod
    def _open_protocol(link: str):
        if sys.platform == "win32":
            os.startfile(link)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, link])

    @staticmethod
    def _compress_data(data: str) -> str:
        compress = zlib.compressobj(zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, 15, 8, 0)
        compressed_data = compress.compress(data.encode())
        compressed_data += compress.flush()
        return urllib.parse.quote(base64.b64encode(compressed_data).decode())
