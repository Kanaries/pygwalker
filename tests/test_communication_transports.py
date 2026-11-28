import asyncio
import json

from pygwalker.communications import gradio_comm
from pygwalker.communications.anywidget_comm import AnywidgetCommunication
from pygwalker.communications.base import BaseCommunication
from pygwalker.communications.hacker_comm import HackerCommunication
from pygwalker.errors import ErrorCode


class _FakeWidget:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


def _decode_widget_response(widget):
    assert widget.sent[0]["type"] == "pyg_response"
    return json.loads(widget.sent[0]["data"])


def test_anywidget_transport_returns_protocol_error_for_missing_action():
    comm = AnywidgetCommunication("widget-gid")
    widget = _FakeWidget()
    comm.widget = widget

    comm._on_mesage(None, {"type": "pyg_request", "msg": {"rid": "request-1", "data": {}}}, [])

    message = _decode_widget_response(widget)
    assert message["action"] == "finish_request"
    assert message["rid"] == "request-1"
    assert message["data"]["code"] == ErrorCode.INVALID_REQUEST
    assert "action" in message["data"]["message"]


def test_hacker_transport_returns_protocol_error_for_missing_action():
    comm = HackerCommunication.__new__(HackerCommunication)
    BaseCommunication.__init__(comm, "hacker-gid")
    comm._HackerCommunication__increase = 0
    sent = []
    comm.send_msg_async = lambda action, data, rid=None: sent.append({"action": action, "data": data, "rid": rid})

    comm._on_mesage({"new": json.dumps({"rid": "request-1", "data": {}})})

    assert sent == [
        {
            "action": "finish_request",
            "data": {
                "code": ErrorCode.INVALID_REQUEST,
                "data": None,
                "message": sent[0]["data"]["message"],
            },
            "rid": "request-1",
        }
    ]
    assert "action" in sent[0]["data"]["message"]


_VALID_COMM_HEADERS = {"content-type": "application/json", "x-pygwalker-request": "1"}


class _FakeRequest:
    def __init__(self, gid, payload, headers=None, raw_body=None):
        self.path_params = {"gid": gid}
        self._payload = payload
        self.headers = dict(_VALID_COMM_HEADERS if headers is None else headers)
        self._body = raw_body if raw_body is not None else json.dumps(payload).encode("utf-8")
        self.json_calls = 0

    async def json(self):
        self.json_calls += 1
        return self._payload

    async def body(self):
        return self._body


def test_gradio_router_rejects_non_json_content_type_before_dispatch():
    comm = gradio_comm.GradioCommunication("gradio-gid")
    calls = []
    comm.register("ping", lambda data: calls.append(data) or {})
    try:
        response = asyncio.run(
            gradio_comm._pygwalker_router(
                _FakeRequest(
                    "gradio-gid",
                    {"action": "ping"},
                    headers={"content-type": "text/plain", "x-pygwalker-request": "1"},
                )
            )
        )
    finally:
        gradio_comm.gradio_comm_map.pop("gradio-gid", None)

    assert response.status_code == 415
    assert calls == []


def test_gradio_router_rejects_missing_custom_header_before_dispatch():
    comm = gradio_comm.GradioCommunication("gradio-gid")
    calls = []
    comm.register("ping", lambda data: calls.append(data) or {})
    try:
        response = asyncio.run(
            gradio_comm._pygwalker_router(
                _FakeRequest("gradio-gid", {"action": "ping"}, headers={"content-type": "application/json"})
            )
        )
    finally:
        gradio_comm.gradio_comm_map.pop("gradio-gid", None)

    assert response.status_code == 403
    assert calls == []


def test_gradio_router_rejects_invalid_json_body():
    gradio_comm.GradioCommunication("gradio-gid")
    try:
        response = asyncio.run(gradio_comm._pygwalker_router(_FakeRequest("gradio-gid", None, raw_body=b"{not json")))
    finally:
        gradio_comm.gradio_comm_map.pop("gradio-gid", None)

    assert response.status_code == 400
    assert json.loads(response.body)["success"] is False


def test_gradio_router_returns_protocol_error_for_missing_action():
    gradio_comm.GradioCommunication("gradio-gid")
    try:
        response = asyncio.run(gradio_comm._pygwalker_router(_FakeRequest("gradio-gid", {"data": {}})))
    finally:
        gradio_comm.gradio_comm_map.pop("gradio-gid", None)

    payload = json.loads(response.body)
    assert payload["code"] == ErrorCode.INVALID_REQUEST
    assert payload["data"] is None
    assert "action" in payload["message"]


def test_gradio_router_preserves_successful_envelope_routing():
    comm = gradio_comm.GradioCommunication("gradio-gid")
    comm.register("ping", lambda _: {})
    try:
        response = asyncio.run(gradio_comm._pygwalker_router(_FakeRequest("gradio-gid", {"action": "ping"})))
    finally:
        gradio_comm.gradio_comm_map.pop("gradio-gid", None)

    assert json.loads(response.body) == {"code": 0, "data": {}, "message": "success"}


def test_comm_envelope_accepts_integer_gid_before_dispatch():
    comm = BaseCommunication("123")
    comm.register("ping", lambda _: {})

    response = comm._receive_msg_envelope({"gid": 123, "rid": "request-1", "action": "ping", "data": {}})

    assert response == {"code": 0, "data": {}, "message": "success"}
