from types import SimpleNamespace

import pandas as pd
import pyarrow as pa

from pygwalker.services import data_bridge as data_bridge_module
from pygwalker.services.data_bridge import DataBridge
from pygwalker._constants import JUPYTER_BYTE_LIMIT


class FakeCloudService:
    def __init__(self):
        self.created = []

    def create_cloud_dataset(self, data_parser, name, is_public, temporary):
        self.created.append(
            {
                "data_parser": data_parser,
                "name": name,
                "is_public": is_public,
                "temporary": temporary,
            }
        )
        return "cloud-dataset-id"


def test_data_bridge_initializes_browser_dataframe_path():
    bridge = DataBridge(
        dataset=pd.DataFrame([{"city": "London", "value": 1}]),
        field_specs=[],
        cloud_computation=False,
        kernel_computation=False,
        kanaries_api_key="",
        cloud_service=FakeCloudService(),
    )

    assert bridge.kernel_computation is False
    assert bridge.origin_data_source == [{"city": "London", "value": 1}]
    assert bridge.dataset_type == "pandas_dataframe"
    assert bridge.parse_dsl_type == "client"
    assert [field["fid"] for field in bridge.field_specs] == ["city", "value"]


def test_data_bridge_initializes_pyarrow_table_path():
    bridge = DataBridge(
        dataset=pa.table({"city": ["London"], "value": [1]}),
        field_specs=[],
        cloud_computation=False,
        kernel_computation=False,
        kanaries_api_key="",
        cloud_service=FakeCloudService(),
    )

    assert bridge.kernel_computation is False
    assert bridge.origin_data_source == [{"city": "London", "value": 1}]
    assert bridge.dataset_type == "pyarrow_table"
    assert bridge.parse_dsl_type == "client"
    assert [field["fid"] for field in bridge.field_specs] == ["city", "value"]


def test_data_bridge_initializes_kernel_sample_path():
    bridge = DataBridge(
        dataset=pd.DataFrame([{"city": "London", "value": 1}]),
        field_specs=[],
        cloud_computation=False,
        kernel_computation=True,
        kanaries_api_key="",
        cloud_service=FakeCloudService(),
    )

    assert bridge.kernel_computation is True
    assert bridge.origin_data_source == [{"city": "London", "value": 1}]


def test_data_bridge_auto_enables_kernel_for_large_data(monkeypatch):
    calls = []

    class FakeParser:
        data_size = JUPYTER_BYTE_LIMIT + 1
        raw_fields = [{"fid": "city"}]
        dataset_type = "pandas_dataframe"

        def to_records(self, limit=None):
            calls.append(limit)
            return [{"city": "London"}]

    monkeypatch.setattr(data_bridge_module, "get_parser", lambda *_args, **_kwargs: FakeParser())

    bridge = DataBridge(
        dataset=object(),
        field_specs=[],
        cloud_computation=False,
        kernel_computation=None,
        kanaries_api_key="",
        cloud_service=FakeCloudService(),
    )

    assert bridge.kernel_computation is True
    assert calls == [500]
    assert bridge.origin_data_source == [{"city": "London"}]


def test_data_bridge_routes_cloud_computation_through_cloud_dataset(monkeypatch):
    calls = []

    class FakeParser:
        data_size = 1
        raw_fields = [{"fid": "city"}]
        dataset_type = "pandas_dataframe"

        def to_records(self, limit=None):
            return [{"city": "London"}]

    class FakeCloudParser(FakeParser):
        dataset_type = "cloud_dataset"

    def fake_get_parser(dataset, field_specs, other_params):
        calls.append((dataset, field_specs, other_params))
        if dataset == "cloud-dataset-id":
            return FakeCloudParser()
        return FakeParser()

    monkeypatch.setattr(data_bridge_module, "get_parser", fake_get_parser)
    cloud_service = FakeCloudService()

    bridge = DataBridge(
        dataset=object(),
        field_specs=[],
        cloud_computation=True,
        kernel_computation=None,
        kanaries_api_key="secret",
        cloud_service=cloud_service,
    )

    assert calls[0][0] != "cloud-dataset-id"
    assert calls[0][2] == {"kanaries_api_key": "secret"}
    assert calls[1][0] == "cloud-dataset-id"
    assert cloud_service.created[0]["temporary"] is True
    assert bridge.dataset_type == "cloud_dataset"
    assert bridge.parse_dsl_type == "server"


def test_data_bridge_parse_dsl_type_tracks_dataset_location():
    assert DataBridge.get_parse_dsl_type(SimpleNamespace(dataset_type="connector_database")) == "server"
    assert DataBridge.get_parse_dsl_type(SimpleNamespace(dataset_type="cloud_dataset")) == "server"
    assert DataBridge.get_parse_dsl_type(SimpleNamespace(dataset_type="pandas_dataframe")) == "client"
