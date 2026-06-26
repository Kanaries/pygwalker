from __future__ import annotations

import sys
from pathlib import Path
from types import UnionType
from typing import Any, Dict, List, Type, Union, get_args, get_origin

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pygwalker.communications import protocol  # noqa: E402


OUTPUT_PATH = REPO_ROOT / "app/src/interfaces/comm.generated.ts"

MODEL_TS_NAMES = {
    protocol.CommMessageRequest: "ICommEnvelope",
    protocol.CommResponse: "ICommResponse",
    protocol.EmptyRequest: "ICommEmptyRequest",
    protocol.SqlQueryRequest: "ICommSqlQueryRequest",
    protocol.PayloadQueryRequest: "ICommPayloadQueryRequest",
    protocol.BatchSqlQueryRequest: "ICommBatchQueryRequest",
    protocol.BatchPayloadQueryRequest: "ICommBatchQueryRequest",
    protocol.UploadSpecToCloudRequest: "ICommUploadSpecToCloudRequest",
    protocol.ChartImageRequest: "ICommChartImageRequest",
    protocol.SaveChartRequest: "ICommSaveChartRequest",
    protocol.UpdateSpecRequest: "ICommUpdateSpecRequest",
    protocol.AskSpecRequest: "ICommAskSpecRequest",
    protocol.ChatChartRequest: "ICommChatChartRequest",
    protocol.OpenDesktopRequest: "ICommOpenDesktopRequest",
    protocol.UploadCloudChartRequest: "ICommUploadCloudChartRequest",
    protocol.UploadCloudDashboardRequest: "ICommUploadCloudDashboardRequest",
    protocol.EmptyResponse: "ICommEmptyResponse",
    protocol.LatestVisSpecResponse: "ICommLatestVisSpecResponse",
    protocol.DataRowsResponse: "ICommDataRowsResponse",
    protocol.BatchDataRowsResponse: "ICommBatchDataRowsResponse",
    protocol.UploadSpecToCloudResponse: "ICommUploadSpecToCloudResponse",
    protocol.CloudCallbackResponse: "ICommCloudCallbackResponse",
    protocol.UploadCloudChartResponse: "ICommUploadCloudChartResponse",
    protocol.UploadCloudDashboardResponse: "ICommUploadCloudDashboardResponse",
}

FIELD_TYPE_OVERRIDES = {
    (protocol.PayloadQueryRequest, "payload"): "IDataQueryPayload",
    (protocol.BatchPayloadQueryRequest, "query_list"): "IDataQueryPayload[]",
    (protocol.DataRowsResponse, "datas"): "IRow[]",
    (protocol.BatchDataRowsResponse, "datas"): "IRow[][]",
    (protocol.AskSpecRequest, "metas"): "IViewField[]",
    (protocol.ChatChartRequest, "metas"): "IViewField[]",
    (protocol.ChatChartRequest, "chats"): "IChatMessage[]",
}

MODEL_ORDER = [
    protocol.SqlQueryRequest,
    protocol.PayloadQueryRequest,
    protocol.BatchSqlQueryRequest,
    protocol.UploadSpecToCloudRequest,
    protocol.ChartImageRequest,
    protocol.SaveChartRequest,
    protocol.UpdateSpecRequest,
    protocol.AskSpecRequest,
    protocol.ChatChartRequest,
    protocol.OpenDesktopRequest,
    protocol.UploadCloudChartRequest,
    protocol.UploadCloudDashboardRequest,
    protocol.CommResponse,
    protocol.CommMessageRequest,
    protocol.EmptyRequest,
    protocol.EmptyResponse,
    protocol.LatestVisSpecResponse,
    protocol.DataRowsResponse,
    protocol.BatchDataRowsResponse,
    protocol.UploadSpecToCloudResponse,
    protocol.CloudCallbackResponse,
    protocol.UploadCloudChartResponse,
    protocol.UploadCloudDashboardResponse,
]


def _fields(model_cls: Type[BaseModel]) -> Dict[str, Any]:
    model_fields = getattr(model_cls, "model_fields", None)
    if model_fields is not None:
        return model_fields
    return model_cls.__fields__


def _field_alias(name: str, field: Any) -> str:
    return field.alias or name


def _field_annotation(field: Any) -> Any:
    return getattr(field, "annotation", getattr(field, "outer_type_", Any))


def _field_required(field: Any) -> bool:
    is_required = getattr(field, "is_required", None)
    if callable(is_required):
        return bool(is_required())
    return bool(getattr(field, "required", False))


def _strip_optional(annotation: Any) -> tuple[Any, bool]:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (Union, UnionType) and type(None) in args:
        non_none_args = tuple(arg for arg in args if arg is not type(None))
        if len(non_none_args) == 1:
            return non_none_args[0], True
        return Union[non_none_args], True
    return annotation, False


def _ts_type(annotation: Any) -> str:
    annotation, _ = _strip_optional(annotation)
    origin = get_origin(annotation)
    args = get_args(annotation)

    if annotation is Any:
        return "any"
    if annotation is str:
        return "string"
    if annotation is int or annotation is float:
        return "number"
    if annotation is bool:
        return "boolean"
    if origin in (list, List):
        item_type = _ts_type(args[0] if args else Any)
        return f"{item_type}[]"
    if origin in (dict, Dict):
        value_type = _ts_type(args[1] if len(args) > 1 else Any)
        return f"Record<string, {value_type}>"
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if annotation is protocol.DataQueryPayload:
            return "IDataQueryPayload"
        return MODEL_TS_NAMES[annotation]
    return "any"


def _render_interface(model_cls: Type[BaseModel]) -> str:
    ts_name = MODEL_TS_NAMES[model_cls]
    if model_cls is protocol.EmptyRequest:
        return "export type ICommEmptyRequest = Record<string, never>;\n"
    if model_cls is protocol.EmptyResponse:
        return "export interface ICommEmptyResponse {}\n"
    if model_cls is protocol.BatchSqlQueryRequest:
        return "export interface ICommBatchQueryRequest<TQuery> {\n    queryList: TQuery[];\n}\n"
    if model_cls is protocol.BatchPayloadQueryRequest:
        return ""
    if model_cls is protocol.CommResponse:
        return "export interface ICommResponse<TData = any> {\n    code: number;\n    data?: TData;\n    message: string;\n}\n"
    if model_cls is protocol.CommMessageRequest:
        return (
            "export interface ICommEnvelope<TAction extends string = string, TData = any> {\n"
            "    action: TAction;\n"
            "    data: TData;\n"
            "    rid?: string;\n"
            "    gid?: string | number;\n"
            "}\n"
        )

    lines = [f"export interface {ts_name} {{"]
    for name, field in _fields(model_cls).items():
        annotation = _field_annotation(field)
        _, optional_annotation = _strip_optional(annotation)
        optional = "?" if optional_annotation or not _field_required(field) else ""
        field_type = FIELD_TYPE_OVERRIDES.get((model_cls, name), _ts_type(annotation))
        lines.append(f"    {_field_alias(name, field)}{optional}: {field_type};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _request_type_for_model(model_cls: Type[BaseModel]) -> str:
    if model_cls is protocol.BatchSqlQueryRequest:
        return "ICommBatchQueryRequest<string>"
    if model_cls is protocol.BatchPayloadQueryRequest:
        return "ICommBatchQueryRequest<IDataQueryPayload>"
    return MODEL_TS_NAMES[model_cls]


def _render_map(name: str, mapping: Dict[str, Type[BaseModel]], type_resolver) -> str:
    lines = [f"export interface {name} {{"]
    for action, model_cls in mapping.items():
        lines.append(f"    {action}: {type_resolver(model_cls)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def render() -> str:
    chunks = [
        "/* eslint-disable */\n",
        "// This file is generated by scripts/generate_comm_protocol_ts.py.\n",
        "// Do not edit it by hand; update pygwalker.communications.protocol instead.\n\n",
        "import type { IDataQueryPayload, IChatMessage, IMutField, IRow } from '@kanaries/graphic-walker/interfaces';\n\n",
        "export type IViewField = IMutField;\n\n",
    ]
    chunks.extend(_render_interface(model_cls) + "\n" for model_cls in MODEL_ORDER)
    chunks.append(_render_map("ICommRequestMap", protocol.COMM_REQUEST_MODELS, _request_type_for_model) + "\n")
    chunks.append(_render_map("ICommResponseMap", protocol.COMM_RESPONSE_MODELS, lambda model: MODEL_TS_NAMES[model]))
    chunks.append("\nexport type ICommAction = keyof ICommRequestMap;\n")
    chunks.append(
        "\nexport type ICommRequestEnvelope<TAction extends ICommAction> = "
        "ICommEnvelope<TAction, ICommRequestMap[TAction]>;\n"
    )
    chunks.append(
        '\nexport type ICommResponseEnvelope<TData = any> = ICommEnvelope<"finish_request", ICommResponse<TData>>;\n'
    )
    return "".join(chunks)


def main() -> None:
    OUTPUT_PATH.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()
