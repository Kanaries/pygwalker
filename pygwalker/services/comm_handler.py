from typing import Any, Callable, Dict, Optional, TYPE_CHECKING, Type, TypeVar

import pandas as pd
from pydantic import BaseModel

from pygwalker import __version__
from pygwalker.communications.base import BaseCommunication
from pygwalker.communications.protocol import (
    AskSpecRequest,
    BatchDataRowsResponse,
    BatchPayloadQueryRequest,
    BatchSqlQueryRequest,
    ChatChartRequest,
    DataRowsResponse,
    EmptyResponse,
    LatestVisSpecResponse,
    OpenDesktopRequest,
    PayloadQueryRequest,
    SaveChartRequest,
    SqlQueryRequest,
    UploadCloudChartRequest,
    UploadCloudDashboardRequest,
    UpdateSpecRequest,
    UploadSpecToCloudRequest,
    dump_response,
    validate_request,
)
from pygwalker.services.cloud_communication import CloudCommunicationService
from pygwalker.services.desktop_import import DesktopImportService
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.preview_image import PreviewImageTool
from pygwalker.services.upload_data import BatchUploadDatasToolOnWidgets
from pygwalker.utils.pydantic_compat import model_dump

if TYPE_CHECKING:
    from pygwalker.api.pygwalker import PygWalker


RequestT = TypeVar("RequestT", bound=BaseModel)


class CommHandler:
    """Register and serve frontend communication callbacks for a walker."""

    def __init__(
        self,
        walker: "PygWalker",
        comm: BaseCommunication,
        preview_tool: Optional[PreviewImageTool] = None,
        upload_tool_cls: Callable[[BaseCommunication], BatchUploadDatasToolOnWidgets] = BatchUploadDatasToolOnWidgets,
        desktop_import: Optional[DesktopImportService] = None,
        cloud_communication: Optional[CloudCommunicationService] = None,
    ):
        self.walker = walker
        self.comm = comm
        self.preview_tool = preview_tool
        self.upload_tool = upload_tool_cls(comm)
        self.desktop_import = desktop_import or DesktopImportService()
        self.cloud_communication = cloud_communication or CloudCommunicationService(walker)

    def register(self) -> None:
        self.walker.comm = self.comm

        self.comm.register("get_latest_vis_spec", self.get_latest_vis_spec)
        self.comm.register("request_data", self.request_data)
        self.comm.register("ping", lambda _: {})
        self._register_request("open_in_desktop", OpenDesktopRequest, self.open_in_desktop)

        if self.walker.use_save_tool:
            self._register_request(
                "upload_spec_to_cloud", UploadSpecToCloudRequest, self.cloud_communication.upload_spec_to_cloud
            )
            self._register_request("update_spec", UpdateSpecRequest, self.update_spec)
            self._register_request("save_chart", SaveChartRequest, self.save_chart)

        if self.walker.show_cloud_tool:
            self._register_request(
                "upload_to_cloud_charts", UploadCloudChartRequest, self.cloud_communication.upload_to_cloud_charts
            )
            self._register_request(
                "upload_to_cloud_dashboard",
                UploadCloudDashboardRequest,
                self.cloud_communication.upload_to_cloud_dashboard,
            )
            self._register_request("get_spec_by_text", AskSpecRequest, self.cloud_communication.get_spec_by_text)
            self._register_request("get_chart_by_chats", ChatChartRequest, self.cloud_communication.get_chart_by_chats)

        if self.walker.kernel_computation:
            self._register_request("get_datas", SqlQueryRequest, self.get_datas)
            self._register_request("get_datas_by_payload", PayloadQueryRequest, self.get_datas_by_payload)
            self._register_request("batch_get_datas_by_sql", BatchSqlQueryRequest, self.batch_get_datas_by_sql)
            self._register_request(
                "batch_get_datas_by_payload", BatchPayloadQueryRequest, self.batch_get_datas_by_payload
            )

        if self.walker.is_export_dataframe:
            self._register_request("export_dataframe_by_payload", PayloadQueryRequest, self.export_dataframe_by_payload)
            self._register_request("export_dataframe_by_sql", SqlQueryRequest, self.export_dataframe_by_sql)

    def _register_request(
        self,
        endpoint: str,
        request_model: Type[RequestT],
        handler: Callable[[RequestT], Dict[str, Any]],
    ) -> None:
        def _handle(data: Dict[str, Any]) -> Dict[str, Any]:
            return handler(validate_request(request_model, data))

        self.comm.register(endpoint, _handle)

    def request_data(self, _):
        self.upload_tool.run(
            records=self.walker.origin_data_source,
            sample_data_count=0,
            data_source_id=self.walker.data_source_id,
        )
        return dump_response(EmptyResponse())

    def get_latest_vis_spec(self, _):
        return dump_response(LatestVisSpecResponse(visSpec=self.walker.vis_spec))

    def save_chart(self, request: SaveChartRequest):
        self.walker.spec_manager.save_chart_payload(model_dump(request, by_alias=True))
        return dump_response(EmptyResponse())

    def update_spec(self, request: UpdateSpecRequest):
        self.walker.spec_manager.update_runtime_state(
            vis_spec=request.vis_spec,
            workflow_list=request.workflow_list,
            chart_data=request.chart_data,
            version=__version__,
        )

        if self.walker.use_preview:
            self.preview_tool.async_render_gw_review(self.walker._get_gw_preview_html())

        self.walker.spec_manager.write_back(self.walker.cloud_service, __version__)
        return dump_response(EmptyResponse())

    def get_datas(self, request: SqlQueryRequest):
        datas = self.walker.data_parser.get_datas_by_sql(request.sql)
        return dump_response(DataRowsResponse(datas=datas))

    def get_datas_by_payload(self, request: PayloadQueryRequest):
        datas = self.walker.data_parser.get_datas_by_payload(model_dump(request.payload, exclude_none=True))
        return dump_response(DataRowsResponse(datas=datas))

    def batch_get_datas_by_sql(self, request: BatchSqlQueryRequest):
        result = self.walker.data_parser.batch_get_datas_by_sql(request.query_list)
        return dump_response(BatchDataRowsResponse(datas=result))

    def batch_get_datas_by_payload(self, request: BatchPayloadQueryRequest):
        result = self.walker.data_parser.batch_get_datas_by_payload(
            [model_dump(query, exclude_none=True) for query in request.query_list]
        )
        return dump_response(BatchDataRowsResponse(datas=result))

    def export_dataframe_by_payload(self, request: PayloadQueryRequest):
        df = pd.DataFrame(self.walker.data_parser.get_datas_by_payload(model_dump(request.payload, exclude_none=True)))
        GlobalVarManager.set_last_exported_dataframe(df)
        self.walker._last_exported_dataframe = df
        return dump_response(EmptyResponse())

    def export_dataframe_by_sql(self, request: SqlQueryRequest):
        df = pd.DataFrame(self.walker.data_parser.get_datas_by_sql(request.sql))
        GlobalVarManager.set_last_exported_dataframe(df)
        self.walker._last_exported_dataframe = df
        return dump_response(EmptyResponse())

    def open_in_desktop(self, request: OpenDesktopRequest):
        self.desktop_import.import_to_desktop(
            spec=request.spec,
            fields=request.fields,
            records=self.walker.data_parser.to_records(),
        )
        return dump_response(EmptyResponse())
