import importlib
from types import SimpleNamespace
from unittest import mock

import pytest

from pygwalker.api.pygwalker import PygWalker
from pygwalker.communications.anywidget_comm import AnywidgetCommunication
from pygwalker.communications.base import BaseCommunication
from pygwalker.communications.http_security import BoundedCommMap
from pygwalker.errors import BaseError, ErrorCode, UnsafeSqlError

RAW_SQL_ENDPOINTS = {"get_datas", "batch_get_datas_by_sql", "export_dataframe_by_sql"}
PAYLOAD_ENDPOINTS = {"get_datas_by_payload", "batch_get_datas_by_payload", "export_dataframe_by_payload"}


def _fake_walker(**overrides):
    values = {
        "kernel_computation": True,
        "is_export_dataframe": True,
        "use_save_tool": False,
        "show_cloud_tool": False,
        "parse_dsl_type": "client",
        "comm": None,
        "data_parser": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


# ---- raw SQL endpoint surface ------------------------------------------------------------


def test_server_parsed_walker_does_not_register_raw_sql_endpoints():
    comm = BaseCommunication("server-gid")
    parser = mock.Mock()
    walker = _fake_walker(parse_dsl_type="server", data_parser=parser)
    PygWalker._init_callback(walker, comm)

    endpoints = set(comm._endpoint_map)
    for action in RAW_SQL_ENDPOINTS:
        assert comm._receive_msg(action, {"sql": "SELECT 1", "queryList": []})["message"] == f"Unknown action: {action}"
    assert not parser.mock_calls
    assert endpoints.isdisjoint(RAW_SQL_ENDPOINTS)
    assert PAYLOAD_ENDPOINTS <= endpoints


def test_client_parsed_walker_keeps_raw_sql_endpoints():
    comm = BaseCommunication("client-gid")
    PygWalker._init_callback(_fake_walker(parse_dsl_type="client"), comm)

    endpoints = set(comm._endpoint_map)
    assert RAW_SQL_ENDPOINTS <= endpoints
    assert PAYLOAD_ENDPOINTS <= endpoints


# ---- open_in_desktop surface ------------------------------------------------------------


def test_local_transports_still_register_open_in_desktop():
    for comm in (BaseCommunication("local-gid"), AnywidgetCommunication("widget-gid")):
        PygWalker._init_callback(_fake_walker(), comm)
        assert "open_in_desktop" in comm._endpoint_map


def _assert_desktop_disabled(comm):
    parser = mock.Mock()
    PygWalker._init_callback(_fake_walker(data_parser=parser), comm)
    assert "open_in_desktop" not in comm._endpoint_map
    response = comm._receive_msg("open_in_desktop", {"fields": [], "spec": {}})
    assert response["message"] == "Unknown action: open_in_desktop"
    parser.to_records.assert_not_called()
    assert comm._receive_msg("ping", {})["code"] == 0


def test_gradio_and_reflex_transports_do_not_register_open_in_desktop():
    pytest.importorskip("starlette")
    pytest.importorskip("fastapi")
    from pygwalker.communications import gradio_comm, reflex_comm

    cases = [
        (gradio_comm.GradioCommunication, gradio_comm.gradio_comm_map),
        (reflex_comm.ReflexCommunication, reflex_comm.reflex_comm_map),
    ]
    for comm_cls, comm_map in cases:
        assert comm_cls.allow_open_in_desktop is False
        comm = comm_cls("hardening-gid")
        try:
            _assert_desktop_disabled(comm)
        finally:
            comm_map.pop("hardening-gid", None)


def test_streamlit_transport_does_not_register_open_in_desktop():
    pytest.importorskip("streamlit")
    pytest.importorskip("tornado")
    streamlit_comm = importlib.import_module("pygwalker.communications.streamlit_comm")

    assert streamlit_comm.StreamlitCommunication.allow_open_in_desktop is False
    comm = streamlit_comm.StreamlitCommunication("hardening-gid")
    try:
        _assert_desktop_disabled(comm)
    finally:
        streamlit_comm.streamlit_comm_map.pop("hardening-gid", None)


# ---- comm lifecycle ---------------------------------------------------------------------


def test_comm_close_releases_walker_data_parser_once():
    parser = mock.Mock()
    comm = BaseCommunication("close-gid")
    PygWalker._init_callback(_fake_walker(data_parser=parser), comm)

    comm.close()
    comm.close()

    parser.close.assert_called_once_with()


def test_comm_close_tolerates_parser_without_close_and_errors():
    comm = BaseCommunication("close-gid")
    PygWalker._init_callback(_fake_walker(data_parser=object()), comm)
    comm.close()

    failing_parser = mock.Mock()
    failing_parser.close.side_effect = RuntimeError("boom")
    comm = BaseCommunication("close-gid")
    PygWalker._init_callback(_fake_walker(data_parser=failing_parser), comm)
    comm.close()  # must not raise
    failing_parser.close.assert_called_once_with()


def test_bounded_comm_map_closes_overwritten_and_evicted_comms():
    comm_map = BoundedCommMap(maxsize=2)
    first, replacement, second, third = (mock.Mock() for _ in range(4))

    comm_map["a"] = first
    comm_map["a"] = first  # same object: not closed
    first.close.assert_not_called()

    comm_map["a"] = replacement
    first.close.assert_called_once_with()

    comm_map["b"] = second
    comm_map["c"] = third  # evicts the oldest entry ("a")
    replacement.close.assert_called_once_with()
    second.close.assert_not_called()
    third.close.assert_not_called()

    assert list(comm_map) == ["b", "c"]
    assert comm_map.get("a") is None
    assert "b" in comm_map and comm_map["c"] is third
    assert comm_map.pop("b") is second
    comm_map.clear()
    assert len(comm_map) == 0


def test_bounded_comm_map_survives_comm_close_errors():
    comm_map = BoundedCommMap(maxsize=1)
    broken = mock.Mock()
    broken.close.side_effect = RuntimeError("boom")
    comm_map["a"] = broken
    comm_map["b"] = object()  # evicts "a"; error is logged, not raised

    assert list(comm_map) == ["b"]


# ---- error sanitization -----------------------------------------------------------------


def _comm_raising(error):
    comm = BaseCommunication("errors")

    def _raise(_data):
        raise error

    comm.register("boom", _raise)
    return comm


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("Conversion Error: Could not convert string 'SECRET_VALUE' to INT32"),
        AttributeError("'NoneType' object has no attribute 'SECRET_VALUE'"),
        OSError("/home/user/SECRET_VALUE/credentials.json: permission denied"),
    ],
)
def test_error_response_hides_raw_exception_text(error, caplog):
    comm = _comm_raising(error)

    with caplog.at_level("ERROR"):
        response = comm._receive_msg("boom", {"sql": "SELECT 'SECRET_VALUE'"})

    assert response == {"code": ErrorCode.UNKNOWN_ERROR, "data": None, "message": "Internal server error"}
    assert "SECRET_VALUE" not in str(response)
    # The full error is still available to the operator in the server log.
    assert "SECRET_VALUE" in caplog.text


def test_error_response_preserves_pygwalker_errors():
    unsafe = _comm_raising(UnsafeSqlError("Only SELECT statements are allowed"))
    response = unsafe._receive_msg("boom", {"sql": "DROP TABLE x"})
    assert response["code"] == ErrorCode.INVALID_REQUEST
    assert response["message"] == "Only SELECT statements are allowed"
    assert response["data"] == {"sql": "DROP TABLE x"}

    token = _comm_raising(BaseError("token invalid", code=ErrorCode.TOKEN_ERROR))
    response = token._receive_msg("boom", {})
    assert response["code"] == ErrorCode.TOKEN_ERROR
    assert response["message"] == "token invalid"
