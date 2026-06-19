import json
from types import SimpleNamespace

from pygwalker import __version__
from pygwalker.communications.protocol import (
    AskSpecRequest,
    ChatChartRequest,
    UploadCloudChartRequest,
    UploadCloudDashboardRequest,
    UploadSpecToCloudRequest,
)
from pygwalker.services import cloud_communication as cloud_communication_module
from pygwalker.services.cloud_communication import CloudCommunicationService
from pygwalker.services.global_var import GlobalVarManager


def test_cloud_communication_upload_spec_updates_token_and_writes_workspace(monkeypatch):
    previous_token = GlobalVarManager.kanaries_api_key
    config_updates = []
    writes = []
    walker = SimpleNamespace(
        spec_manager=SimpleNamespace(build_spec_obj=lambda version: {"version": version, "config": []}),
        cloud_service=SimpleNamespace(
            get_kanaries_user_info=lambda: {"workspaceName": "workspace"},
            write_config_to_cloud=lambda path, data: writes.append((path, json.loads(data))),
        ),
    )
    monkeypatch.setattr(cloud_communication_module, "set_config", lambda config: config_updates.append(config))

    try:
        response = CloudCommunicationService(walker).upload_spec_to_cloud(
            UploadSpecToCloudRequest(fileName="chart.json", newToken="new-token")
        )
    finally:
        GlobalVarManager.kanaries_api_key = previous_token

    assert response == {"specFilePath": "workspace/chart.json"}
    assert config_updates == [{"kanaries_token": "new-token"}]
    assert writes == [("workspace/chart.json", {"version": __version__, "config": []})]


def test_cloud_communication_uses_custom_text_callbacks():
    ask_calls = []
    chat_calls = []
    walker = SimpleNamespace(
        other_props={
            "custom_ask_callback": lambda metas, query: ask_calls.append((metas, query)) or {"chart": "bar"},
            "custom_chat_callback": lambda metas, chats: chat_calls.append((metas, chats)) or {"chart": "line"},
        },
        cloud_service=SimpleNamespace(),
    )
    service = CloudCommunicationService(walker)

    ask_response = service.get_spec_by_text(AskSpecRequest(metas=[{"fid": "city"}], query="show city"))
    chat_response = service.get_chart_by_chats(
        ChatChartRequest(metas=[{"fid": "city"}], chats=[{"role": "user", "content": "show city"}])
    )

    assert ask_response == {"data": {"chart": "bar"}}
    assert chat_response == {"data": {"chart": "line"}}
    assert ask_calls == [([{"fid": "city"}], "show city")]
    assert chat_calls == [([{"fid": "city"}], [{"role": "user", "content": "show city"}])]


def test_cloud_communication_uploads_chart_and_dashboard():
    upload_chart_calls = []
    upload_dashboard_calls = []
    walker = SimpleNamespace(
        data_parser=object(),
        appearance="light",
        cloud_service=SimpleNamespace(
            upload_cloud_chart=lambda **kwargs: (
                upload_chart_calls.append(kwargs) or {"chart_id": "chart-id", "dataset_id": "dataset-id"}
            ),
            upload_cloud_dashboard=lambda **kwargs: (
                upload_dashboard_calls.append(kwargs) or {"dashboard_id": "dashboard-id", "dataset_id": "dataset-id"}
            ),
        ),
    )
    service = CloudCommunicationService(walker)

    chart_response = service.upload_to_cloud_charts(
        UploadCloudChartRequest(
            chartName="Chart",
            datasetName="Dataset",
            isPublic=True,
            visSpec=[{"name": "Chart"}],
            workflow=[{"type": "view"}],
        )
    )
    dashboard_response = service.upload_to_cloud_dashboard(
        UploadCloudDashboardRequest(
            chartName="Dashboard",
            datasetName="Dataset",
            isPublic=False,
            isCreateDashboard=True,
            visSpec=[{"name": "Chart"}],
            workflowList=[[{"type": "view"}]],
        )
    )

    assert chart_response == {"chartId": "chart-id", "datasetId": "dataset-id"}
    assert dashboard_response == {"dashboardId": "dashboard-id", "datasetId": "dataset-id"}
    assert upload_chart_calls == [
        {
            "data_parser": walker.data_parser,
            "chart_name": "Chart",
            "dataset_name": "Dataset",
            "workflow": [{"type": "view"}],
            "spec_list": [{"name": "Chart"}],
            "is_public": True,
        }
    ]
    assert upload_dashboard_calls == [
        {
            "data_parser": walker.data_parser,
            "dashboard_name": "Dashboard",
            "dataset_name": "Dataset",
            "workflow_list": [[{"type": "view"}]],
            "spec_list": [{"name": "Chart"}],
            "is_public": False,
            "create_dashboard_flag": True,
            "appearance": "light",
        }
    ]
