from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, ValidationError

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - only exercised on pydantic v1
    ConfigDict = None

from pygwalker.errors import CommProtocolError
from pygwalker.utils.pydantic_compat import model_dump, model_validate


def validate_request(model_cls: Type[BaseModel], data: Dict[str, Any]) -> BaseModel:
    try:
        return model_validate(model_cls, data)
    except ValidationError as exc:
        raise CommProtocolError(f"Invalid communication payload: {exc}") from exc


def dump_response(response: BaseModel) -> Dict[str, Any]:
    return model_dump(response, by_alias=True, exclude_none=True)


if ConfigDict is not None:

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
    gid: Optional[str] = None


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


class UpdateSpecRequest(CommBaseModel):
    vis_spec: List[Dict[str, Any]] = Field(..., alias="visSpec")
    chart_data: Dict[str, Any] = Field(..., alias="chartData")
    workflow_list: List[Dict[str, Any]] = Field(default_factory=list, alias="workflowList")


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
