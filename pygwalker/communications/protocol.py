from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, ValidationError

from pygwalker.errors import CommProtocolError
from pygwalker.utils.pydantic_compat import model_validate


def validate_request(model_cls: Type[BaseModel], data: Dict[str, Any]) -> BaseModel:
    try:
        return model_validate(model_cls, data)
    except ValidationError as exc:
        raise CommProtocolError(f"Invalid communication payload: {exc}") from exc


class DataQueryPayload(BaseModel):
    workflow: List[Dict[str, Any]]
    tag: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class SqlQueryRequest(BaseModel):
    sql: str


class PayloadQueryRequest(BaseModel):
    payload: DataQueryPayload


class BatchSqlQueryRequest(BaseModel):
    query_list: List[str] = Field(..., alias="queryList")


class BatchPayloadQueryRequest(BaseModel):
    query_list: List[DataQueryPayload] = Field(..., alias="queryList")


class UpdateSpecRequest(BaseModel):
    vis_spec: List[Dict[str, Any]] = Field(..., alias="visSpec")
    chart_data: Dict[str, Any] = Field(..., alias="chartData")
    workflow_list: List[Dict[str, Any]] = Field(default_factory=list, alias="workflowList")


class UploadSpecToCloudRequest(BaseModel):
    file_name: str = Field(..., alias="fileName")
    new_token: str = Field("", alias="newToken")


class ChartImageRequest(BaseModel):
    row_index: int = Field(..., alias="rowIndex")
    col_index: int = Field(..., alias="colIndex")
    data: str
    height: int
    width: int
    canvas_height: int = Field(..., alias="canvasHeight")
    canvas_width: int = Field(..., alias="canvasWidth")


class SaveChartRequest(BaseModel):
    charts: List[ChartImageRequest]
    single_chart: str = Field(..., alias="singleChart")
    n_rows: int = Field(..., alias="nRows")
    n_cols: int = Field(..., alias="nCols")
    title: str


class AskSpecRequest(BaseModel):
    metas: List[Dict[str, Any]]
    query: str


class ChatChartRequest(BaseModel):
    metas: List[Dict[str, Any]]
    chats: List[Dict[str, Any]]


class OpenDesktopRequest(BaseModel):
    spec: List[Dict[str, Any]]
    fields: List[Dict[str, Any]]
