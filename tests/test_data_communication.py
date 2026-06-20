from types import SimpleNamespace

from pygwalker.communications.protocol import (
    BatchPayloadQueryRequest,
    BatchSqlQueryRequest,
    PayloadQueryRequest,
    SqlQueryRequest,
)
from pygwalker.services.data_communication import DataCommunicationService
from pygwalker.services.global_var import GlobalVarManager


def test_data_communication_queries_sql_and_payload():
    calls = []
    walker = SimpleNamespace(
        data_parser=SimpleNamespace(
            get_datas_by_sql=lambda sql: calls.append(("sql", sql)) or [{"total": 3}],
            get_datas_by_payload=lambda payload: calls.append(("payload", payload)) or [{"city": "London"}],
        )
    )
    service = DataCommunicationService(walker)

    sql_response = service.get_datas(SqlQueryRequest(sql="SELECT 1"))
    payload_response = service.get_datas_by_payload(
        PayloadQueryRequest(payload={"workflow": [{"type": "view"}], "limit": 5})
    )

    assert sql_response == {"datas": [{"total": 3}]}
    assert payload_response == {"datas": [{"city": "London"}]}
    assert calls == [
        ("sql", "SELECT 1"),
        ("payload", {"workflow": [{"type": "view"}], "limit": 5}),
    ]


def test_data_communication_queries_batches():
    calls = []
    walker = SimpleNamespace(
        data_parser=SimpleNamespace(
            batch_get_datas_by_sql=lambda queries: calls.append(("sql", queries)) or [[{"total": 3}]],
            batch_get_datas_by_payload=lambda payloads: calls.append(("payload", payloads)) or [[{"city": "London"}]],
        )
    )
    service = DataCommunicationService(walker)

    sql_response = service.batch_get_datas_by_sql(BatchSqlQueryRequest(queryList=["SELECT 1"]))
    payload_response = service.batch_get_datas_by_payload(
        BatchPayloadQueryRequest(queryList=[{"workflow": [{"type": "view"}], "offset": 2}])
    )

    assert sql_response == {"datas": [[{"total": 3}]]}
    assert payload_response == {"datas": [[{"city": "London"}]]}
    assert calls == [
        ("sql", ["SELECT 1"]),
        ("payload", [{"workflow": [{"type": "view"}], "offset": 2}]),
    ]


def test_data_communication_exports_dataframe_to_walker_and_global_state():
    previous_exported_dataframe = GlobalVarManager.last_exported_dataframe
    walker = SimpleNamespace(
        _last_exported_dataframe=None,
        data_parser=SimpleNamespace(
            get_datas_by_sql=lambda _sql: [{"city": "Tokyo", "value": 2}],
            get_datas_by_payload=lambda _payload: [{"city": "London", "value": 1}],
        ),
    )
    service = DataCommunicationService(walker)

    try:
        sql_response = service.export_dataframe_by_sql(SqlQueryRequest(sql="SELECT *"))

        assert sql_response == {}
        assert walker._last_exported_dataframe.to_dict("records") == [{"city": "Tokyo", "value": 2}]
        assert GlobalVarManager.last_exported_dataframe is walker._last_exported_dataframe

        payload_response = service.export_dataframe_by_payload(
            PayloadQueryRequest(payload={"workflow": [{"type": "view"}]})
        )

        assert payload_response == {}
        assert walker._last_exported_dataframe.to_dict("records") == [{"city": "London", "value": 1}]
        assert GlobalVarManager.last_exported_dataframe is walker._last_exported_dataframe
    finally:
        GlobalVarManager.last_exported_dataframe = previous_exported_dataframe
