import json
from typing import TYPE_CHECKING

from pygwalker import __version__
from pygwalker.communications.protocol import (
    AskSpecRequest,
    ChatChartRequest,
    CloudCallbackResponse,
    UploadCloudChartResponse,
    UploadCloudDashboardResponse,
    UploadCloudChartRequest,
    UploadCloudDashboardRequest,
    UploadSpecToCloudResponse,
    UploadSpecToCloudRequest,
    dump_response,
)
from pygwalker.services.config import set_config
from pygwalker.services.global_var import GlobalVarManager

if TYPE_CHECKING:
    from pygwalker.api.pygwalker import PygWalker


class CloudCommunicationService:
    """Serve cloud-related communication endpoints for a walker."""

    def __init__(self, walker: "PygWalker"):
        self.walker = walker

    def upload_spec_to_cloud(self, request: UploadSpecToCloudRequest):
        if request.new_token:
            set_config({"kanaries_token": request.new_token})
            GlobalVarManager.kanaries_api_key = request.new_token
        spec_obj = self.walker.spec_manager.build_spec_obj(__version__)
        workspace_name = self.walker.cloud_service.get_kanaries_user_info()["workspaceName"]
        path = f"{workspace_name}/{request.file_name}"
        self.walker.cloud_service.write_config_to_cloud(path, json.dumps(spec_obj))
        return dump_response(UploadSpecToCloudResponse(specFilePath=path))

    def get_spec_by_text(self, request: AskSpecRequest):
        callback = self.walker.other_props.get("custom_ask_callback")
        if callback is None:
            callback = self.walker.cloud_service.get_spec_by_text
        return dump_response(CloudCallbackResponse(data=callback(request.metas, request.query)))

    def get_chart_by_chats(self, request: ChatChartRequest):
        callback = self.walker.other_props.get("custom_chat_callback")
        if callback is None:
            callback = self.walker.cloud_service.get_chart_by_chats
        return dump_response(CloudCallbackResponse(data=callback(request.metas, request.chats)))

    def upload_to_cloud_charts(self, request: UploadCloudChartRequest):
        result = self.walker.cloud_service.upload_cloud_chart(
            data_parser=self.walker.data_parser,
            chart_name=request.chart_name,
            dataset_name=request.dataset_name,
            workflow=request.workflow,
            spec_list=request.vis_spec,
            is_public=request.is_public,
        )
        return dump_response(UploadCloudChartResponse(chartId=result["chart_id"], datasetId=result["dataset_id"]))

    def upload_to_cloud_dashboard(self, request: UploadCloudDashboardRequest):
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
        return dump_response(
            UploadCloudDashboardResponse(dashboardId=result["dashboard_id"], datasetId=result["dataset_id"])
        )
