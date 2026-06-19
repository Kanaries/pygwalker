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
