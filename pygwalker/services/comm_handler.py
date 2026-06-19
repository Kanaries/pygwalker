from typing import Any, Callable, Dict, Optional, TYPE_CHECKING, Type, TypeVar

from pydantic import BaseModel

from pygwalker.communications.base import BaseCommunication
from pygwalker.communications.protocol import (
    AskSpecRequest,
    BatchPayloadQueryRequest,
    BatchSqlQueryRequest,
    ChatChartRequest,
    EmptyResponse,
    EmptyRequest,
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
from pygwalker.services.data_communication import DataCommunicationService
from pygwalker.services.data_upload_communication import DataUploadCommunicationService
from pygwalker.services.desktop_communication import DesktopCommunicationService
from pygwalker.services.desktop_import import DesktopImportService
from pygwalker.services.preview_image import PreviewImageTool
from pygwalker.services.spec_communication import SpecCommunicationService
from pygwalker.services.upload_data import BatchUploadDatasToolOnWidgets

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
        desktop_communication: Optional[DesktopCommunicationService] = None,
        desktop_import: Optional[DesktopImportService] = None,
        cloud_communication: Optional[CloudCommunicationService] = None,
        data_communication: Optional[DataCommunicationService] = None,
        data_upload_communication: Optional[DataUploadCommunicationService] = None,
        spec_communication: Optional[SpecCommunicationService] = None,
    ):
        self.walker = walker
        self.comm = comm
        self.preview_tool = preview_tool
        self.desktop_communication = desktop_communication or DesktopCommunicationService(walker, desktop_import)
        self.cloud_communication = cloud_communication or CloudCommunicationService(walker)
        self.data_communication = data_communication or DataCommunicationService(walker)
        self.data_upload_communication = data_upload_communication or DataUploadCommunicationService(
            walker,
            upload_tool_cls(comm),
        )
        self.spec_communication = spec_communication or SpecCommunicationService(walker, preview_tool)

    def register(self) -> None:
        self.walker.comm = self.comm

        self._register_request("get_latest_vis_spec", EmptyRequest, self.spec_communication.get_latest_vis_spec)
        self._register_request("request_data", EmptyRequest, self.data_upload_communication.request_data)
        self._register_request("ping", EmptyRequest, self._ping)
        self._register_request("open_in_desktop", OpenDesktopRequest, self.desktop_communication.open_in_desktop)

        if self.walker.use_save_tool:
            self._register_request(
                "upload_spec_to_cloud", UploadSpecToCloudRequest, self.cloud_communication.upload_spec_to_cloud
            )
            self._register_request("update_spec", UpdateSpecRequest, self.spec_communication.update_spec)
            self._register_request("save_chart", SaveChartRequest, self.spec_communication.save_chart)

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
            self._register_request("get_datas", SqlQueryRequest, self.data_communication.get_datas)
            self._register_request(
                "get_datas_by_payload", PayloadQueryRequest, self.data_communication.get_datas_by_payload
            )
            self._register_request(
                "batch_get_datas_by_sql", BatchSqlQueryRequest, self.data_communication.batch_get_datas_by_sql
            )
            self._register_request(
                "batch_get_datas_by_payload",
                BatchPayloadQueryRequest,
                self.data_communication.batch_get_datas_by_payload,
            )

        if self.walker.is_export_dataframe:
            self._register_request(
                "export_dataframe_by_payload",
                PayloadQueryRequest,
                self.data_communication.export_dataframe_by_payload,
            )
            self._register_request(
                "export_dataframe_by_sql", SqlQueryRequest, self.data_communication.export_dataframe_by_sql
            )

    def _register_request(
        self,
        endpoint: str,
        request_model: Type[RequestT],
        handler: Callable[[RequestT], Dict[str, Any]],
    ) -> None:
        def _handle(data: Dict[str, Any]) -> Dict[str, Any]:
            return handler(validate_request(request_model, data))

        self.comm.register(endpoint, _handle)

    def _ping(self, _: EmptyRequest) -> Dict[str, Any]:
        return dump_response(EmptyResponse())
