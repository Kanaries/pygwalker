from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, ValidationError

from pygwalker.utils.pydantic_compat import PYDANTIC_V2, model_dump, model_validate

from pygwalker.errors import CommProtocolError

if PYDANTIC_V2:
    from pydantic import ConfigDict


def validate_request(model_cls: Type[BaseModel], data: Dict[str, Any]) -> BaseModel:
    try:
        return model_validate(model_cls, data)
    except ValidationError as exc:
        raise CommProtocolError(f"Invalid communication payload: {exc}") from exc


def dump_response(response: BaseModel) -> Dict[str, Any]:
    return model_dump(response, by_alias=True, exclude_none=True)


def dump_comm_response(response: BaseModel) -> Dict[str, Any]:
    return model_dump(response, by_alias=True)


if PYDANTIC_V2:

    class CommBaseModel(BaseModel):
        model_config = ConfigDict(extra="forbid")

else:

    class CommBaseModel(BaseModel):
        class Config:
            extra = "forbid"


class DataQueryPayload(CommBaseModel):
    workflow: List[Dict[str, Any]]
    tag: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class CommMessageRequest(CommBaseModel):
    action: str
    data: Dict[str, Any] = Field(default_factory=dict)
    rid: Optional[str] = None
    gid: Optional[Union[int, str]] = None


class CommResponse(CommBaseModel):
    code: int
    data: Any = None
    message: str


class EmptyRequest(CommBaseModel):
    pass


class SqlQueryRequest(CommBaseModel):
    sql: str


class PayloadQueryRequest(CommBaseModel):
    payload: DataQueryPayload


class BatchSqlQueryRequest(CommBaseModel):
    query_list: List[str] = Field(..., alias="queryList")


class BatchPayloadQueryRequest(CommBaseModel):
    query_list: List[DataQueryPayload] = Field(..., alias="queryList")


class UploadSpecToCloudRequest(CommBaseModel):
    file_name: str = Field(..., alias="fileName")
    new_token: str = Field("", alias="newToken")


class ChartImageRequest(CommBaseModel):
    row_index: int = Field(..., alias="rowIndex")
    col_index: int = Field(..., alias="colIndex")
    data: str
    height: int
    width: int
    canvas_height: int = Field(..., alias="canvasHeight")
    canvas_width: int = Field(..., alias="canvasWidth")


class SaveChartRequest(CommBaseModel):
    charts: List[ChartImageRequest]
    single_chart: str = Field(..., alias="singleChart")
    n_rows: int = Field(..., alias="nRows")
    n_cols: int = Field(..., alias="nCols")
    title: str


class UpdateSpecRequest(CommBaseModel):
    vis_spec: List[Dict[str, Any]] = Field(..., alias="visSpec")
    chart_data: SaveChartRequest = Field(..., alias="chartData")
    workflow_list: List[Dict[str, Any]] = Field(default_factory=list, alias="workflowList")


class AskSpecRequest(CommBaseModel):
    metas: List[Dict[str, Any]]
    query: str


class ChatChartRequest(CommBaseModel):
    metas: List[Dict[str, Any]]
    chats: List[Dict[str, Any]]


class OpenDesktopRequest(CommBaseModel):
    spec: List[Dict[str, Any]]
    fields: List[Dict[str, Any]]


class UploadCloudChartRequest(CommBaseModel):
    chart_name: str = Field(..., alias="chartName")
    dataset_name: str = Field(..., alias="datasetName")
    is_public: bool = Field(..., alias="isPublic")
    vis_spec: List[Dict[str, Any]] = Field(..., alias="visSpec")
    workflow: List[Dict[str, Any]]


class UploadCloudDashboardRequest(CommBaseModel):
    chart_name: str = Field(..., alias="chartName")
    dataset_name: str = Field(..., alias="datasetName")
    is_public: bool = Field(..., alias="isPublic")
    is_create_dashboard: bool = Field(..., alias="isCreateDashboard")
    vis_spec: List[Dict[str, Any]] = Field(..., alias="visSpec")
    workflow_list: List[List[Dict[str, Any]]] = Field(..., alias="workflowList")


class EmptyResponse(CommBaseModel):
    pass


class LatestVisSpecResponse(CommBaseModel):
    vis_spec: List[Dict[str, Any]] = Field(..., alias="visSpec")


class DataRowsResponse(CommBaseModel):
    datas: List[Dict[str, Any]]


class BatchDataRowsResponse(CommBaseModel):
    datas: List[List[Dict[str, Any]]]


class UploadSpecToCloudResponse(CommBaseModel):
    spec_file_path: str = Field(..., alias="specFilePath")


class CloudCallbackResponse(CommBaseModel):
    data: Any


class UploadCloudChartResponse(CommBaseModel):
    chart_id: str = Field(..., alias="chartId")
    dataset_id: str = Field(..., alias="datasetId")


class UploadCloudDashboardResponse(CommBaseModel):
    dashboard_id: str = Field(..., alias="dashboardId")
    dataset_id: str = Field(..., alias="datasetId")


COMM_REQUEST_MODELS: Dict[str, Type[BaseModel]] = {
    "ping": EmptyRequest,
    "request_data": EmptyRequest,
    "get_latest_vis_spec": EmptyRequest,
    "save_chart": SaveChartRequest,
    "update_spec": UpdateSpecRequest,
    "upload_spec_to_cloud": UploadSpecToCloudRequest,
    "get_datas": SqlQueryRequest,
    "get_datas_by_payload": PayloadQueryRequest,
    "batch_get_datas_by_sql": BatchSqlQueryRequest,
    "batch_get_datas_by_payload": BatchPayloadQueryRequest,
    "get_spec_by_text": AskSpecRequest,
    "get_chart_by_chats": ChatChartRequest,
    "export_dataframe_by_payload": PayloadQueryRequest,
    "export_dataframe_by_sql": SqlQueryRequest,
    "upload_to_cloud_charts": UploadCloudChartRequest,
    "upload_to_cloud_dashboard": UploadCloudDashboardRequest,
    "open_in_desktop": OpenDesktopRequest,
}

COMM_RESPONSE_MODELS: Dict[str, Type[BaseModel]] = {
    "ping": EmptyResponse,
    "request_data": EmptyResponse,
    "get_latest_vis_spec": LatestVisSpecResponse,
    "save_chart": EmptyResponse,
    "update_spec": EmptyResponse,
    "upload_spec_to_cloud": UploadSpecToCloudResponse,
    "get_datas": DataRowsResponse,
    "get_datas_by_payload": DataRowsResponse,
    "batch_get_datas_by_sql": BatchDataRowsResponse,
    "batch_get_datas_by_payload": BatchDataRowsResponse,
    "get_spec_by_text": CloudCallbackResponse,
    "get_chart_by_chats": CloudCallbackResponse,
    "export_dataframe_by_payload": EmptyResponse,
    "export_dataframe_by_sql": EmptyResponse,
    "upload_to_cloud_charts": UploadCloudChartResponse,
    "upload_to_cloud_dashboard": UploadCloudDashboardResponse,
    "open_in_desktop": EmptyResponse,
}
