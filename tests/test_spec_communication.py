from types import SimpleNamespace

from pygwalker import __version__
from pygwalker.communications.protocol import SaveChartRequest, UpdateSpecRequest
from pygwalker.services.spec_communication import SpecCommunicationService


def _chart_payload(title="Updated chart"):
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


def test_spec_communication_returns_latest_vis_spec():
    walker = SimpleNamespace(vis_spec=[{"name": "Chart"}])

    assert SpecCommunicationService(walker).get_latest_vis_spec({}) == {"visSpec": [{"name": "Chart"}]}


def test_spec_communication_saves_chart_payload():
    saved_payloads = []
    walker = SimpleNamespace(spec_manager=SimpleNamespace(save_chart_payload=saved_payloads.append))

    response = SpecCommunicationService(walker).save_chart(SaveChartRequest(**_chart_payload("Saved chart")))

    assert response == {}
    assert saved_payloads == [_chart_payload("Saved chart")]


def test_spec_communication_updates_runtime_state_writes_back_and_refreshes_preview():
    runtime_updates = []
    write_backs = []
    preview_renders = []
    preview_tool = SimpleNamespace(async_render_gw_review=preview_renders.append)
    walker = SimpleNamespace(
        use_preview=True,
        cloud_service=object(),
        spec_manager=SimpleNamespace(
            update_runtime_state=lambda **kwargs: runtime_updates.append(kwargs),
            write_back=lambda cloud_service, version: write_backs.append((cloud_service, version)),
        ),
        _get_gw_preview_html=lambda: "<div>preview</div>",
    )
    request = UpdateSpecRequest(
        visSpec=[{"name": "Chart"}],
        workflowList=[{"workflow": []}],
        chartData=_chart_payload("Chart"),
    )

    response = SpecCommunicationService(walker, preview_tool).update_spec(request)

    assert response == {}
    assert runtime_updates == [
        {
            "vis_spec": [{"name": "Chart"}],
            "workflow_list": [{"workflow": []}],
            "chart_data": _chart_payload("Chart"),
            "version": __version__,
        }
    ]
    assert write_backs == [(walker.cloud_service, __version__)]
    assert preview_renders == ["<div>preview</div>"]
