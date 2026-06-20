from types import SimpleNamespace

from pygwalker.services.data_upload_communication import DataUploadCommunicationService


def test_data_upload_communication_requests_current_records():
    upload_calls = []
    walker = SimpleNamespace(
        origin_data_source=[{"city": "London"}, {"city": "Tokyo"}],
        data_source_id="data-source",
    )
    upload_tool = SimpleNamespace(run=lambda **kwargs: upload_calls.append(kwargs))

    response = DataUploadCommunicationService(walker, upload_tool).request_data({})

    assert response == {}
    assert upload_calls == [
        {
            "records": [{"city": "London"}, {"city": "Tokyo"}],
            "sample_data_count": 0,
            "data_source_id": "data-source",
        }
    ]
