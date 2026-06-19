from typing import TYPE_CHECKING

import pandas as pd

from pygwalker.communications.protocol import (
    BatchDataRowsResponse,
    BatchPayloadQueryRequest,
    BatchSqlQueryRequest,
    DataRowsResponse,
    EmptyResponse,
    PayloadQueryRequest,
    SqlQueryRequest,
    dump_response,
)
from pygwalker.services.global_var import GlobalVarManager
from pygwalker.utils.pydantic_compat import model_dump

if TYPE_CHECKING:
    from pygwalker.api.pygwalker import PygWalker


class DataCommunicationService:
    """Serve data query and dataframe export communication endpoints."""

    def __init__(self, walker: "PygWalker"):
        self.walker = walker

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
        self._store_exported_dataframe(df)
        return dump_response(EmptyResponse())

    def export_dataframe_by_sql(self, request: SqlQueryRequest):
        df = pd.DataFrame(self.walker.data_parser.get_datas_by_sql(request.sql))
        self._store_exported_dataframe(df)
        return dump_response(EmptyResponse())

    def _store_exported_dataframe(self, df: pd.DataFrame) -> None:
        GlobalVarManager.set_last_exported_dataframe(df)
        self.walker._last_exported_dataframe = df
