import json

from pygwalker.services.spec_manager import SpecManager


RAW_FIELDS = [
    {
        "fid": "city",
        "name": "city",
        "semanticType": "nominal",
        "analyticType": "dimension",
    },
    {
        "fid": "value",
        "name": "value",
        "semanticType": "quantitative",
        "analyticType": "measure",
    },
]


def _vis_spec(name="Chart 1"):
    return [
        {
            "name": name,
            "encodings": {
                "dimensions": [],
                "measures": [],
            },
        }
    ]


def _chart_payload(title="Chart 1"):
    return {
        "charts": [
            {
                "rowIndex": 0,
                "colIndex": 0,
                "data": "data:image/png;base64,abc",
                "height": 100,
                "width": 200,
                "canvasHeight": 100,
                "canvasWidth": 200,
            }
        ],
        "singleChart": "data:image/png;base64,abc",
        "nRows": 1,
        "nCols": 1,
        "title": title,
    }


def test_spec_manager_initializes_spec_state_and_fills_new_fields():
    manager = SpecManager(
        {
            "config": _vis_spec(),
            "chart_map": {},
            "workflow_list": [{"workflow": []}],
            "version": "0.5.0",
        },
        RAW_FIELDS,
    )

    assert manager.spec_type == "json_obj"
    assert manager.spec_version == "0.5.0"
    assert manager.workflow_list == [{"workflow": []}]
    assert manager.chart_name_index_map == {"Chart 1": 0}
    assert [field["fid"] for field in manager.vis_spec[0]["encodings"]["dimensions"]] == ["city"]
    assert [field["fid"] for field in manager.vis_spec[0]["encodings"]["measures"]] == ["value"]


def test_spec_manager_updates_runtime_state_and_saved_chart_map():
    manager = SpecManager("", RAW_FIELDS)
    workflow_list = [{"workflow": [{"type": "view"}]}]

    manager.update_runtime_state(
        vis_spec=_vis_spec("Updated chart"),
        workflow_list=workflow_list,
        chart_data=_chart_payload("Updated chart"),
        version="0.6.0",
    )

    assert manager.spec_version == "0.6.0"
    assert manager.workflow_list == workflow_list
    assert manager.chart_list == ["Updated chart"]
    assert manager.get_chart_by_name("Updated chart").title == "Updated chart"
    assert manager.get_chart_index("Updated chart") == 0
    assert manager.build_spec_obj("0.6.1") == {
        "config": _vis_spec("Updated chart"),
        "chart_map": {},
        "version": "0.6.1",
        "workflow_list": workflow_list,
    }


def test_spec_manager_writes_json_file_specs(tmp_path):
    path = tmp_path / "spec.json"
    path.write_text(json.dumps({"config": [], "chart_map": {}, "workflow_list": [], "version": "0.5.0"}))
    manager = SpecManager(str(path), RAW_FIELDS)
    manager.update_runtime_state(
        vis_spec=_vis_spec("File chart"),
        workflow_list=[{"workflow": [{"type": "view"}]}],
        chart_data=_chart_payload("File chart"),
        version="0.6.0",
    )

    manager.write_back(cloud_service=None, version="0.6.1")

    assert json.loads(path.read_text()) == {
        "config": _vis_spec("File chart"),
        "chart_map": {},
        "version": "0.6.1",
        "workflow_list": [{"workflow": [{"type": "view"}]}],
    }


def test_spec_manager_writes_ksf_cloud_specs():
    manager = SpecManager("", RAW_FIELDS)
    manager.spec = "ksf://workspace/spec.json"
    manager.spec_type = "json_ksf"
    manager.update_runtime_state(
        vis_spec=_vis_spec("Cloud chart"),
        workflow_list=[{"workflow": [{"type": "view"}]}],
        chart_data=_chart_payload("Cloud chart"),
        version="0.6.0",
    )
    writes = []

    class FakeCloudService:
        def write_config_to_cloud(self, path, payload):
            writes.append((path, json.loads(payload)))

    manager.write_back(FakeCloudService(), version="0.6.1")

    assert writes == [
        (
            "workspace/spec.json",
            {
                "config": _vis_spec("Cloud chart"),
                "chart_map": {},
                "version": "0.6.1",
                "workflow_list": [{"workflow": [{"type": "view"}]}],
            },
        )
    ]


def test_spec_manager_loads_saved_chart_map():
    chart_payload = _chart_payload("Saved chart")
    manager = SpecManager(
        {
            "config": [],
            "chart_map": {"Saved chart": chart_payload},
            "workflow_list": [],
            "version": "0.5.0",
        },
        RAW_FIELDS,
    )

    assert manager.chart_list == ["Saved chart"]
    assert manager.get_chart_by_name("Saved chart").title == "Saved chart"
