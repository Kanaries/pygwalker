import asyncio
import http.client
import importlib
import json
import socket
import sys
import threading
from contextlib import contextmanager

import pytest

from pygwalker.api import webserver
from pygwalker.communications.base import BaseCommunication
from pygwalker.communications.http_security import (
    CUSTOM_REQUEST_HEADER,
    MAX_COMM_BODY_BYTES,
    has_custom_request_header,
    is_allowed_local_host,
    is_json_content_type,
    is_same_origin,
    parse_content_length,
)

VALID_COMM_HEADERS = {"Content-Type": "application/json", CUSTOM_REQUEST_HEADER: "1"}
PING = {"action": "ping", "data": {}}


# =========================================================================================
# Pure helpers
# =========================================================================================


@pytest.mark.parametrize(
    "host",
    [
        "localhost",
        "localhost:8080",
        "LOCALHOST:8080",
        "127.0.0.1",
        "127.0.0.1:54321",  # arbitrary / forwarded ports are allowed (SSH -L, docker -p)
        "[::1]",
        "[::1]:8080",
    ],
)
def test_is_allowed_local_host_accepts_loopback(host):
    assert is_allowed_local_host(host) is True


@pytest.mark.parametrize(
    "host",
    [
        None,
        "",
        " ",
        "evil.example",
        "evil.example:8080",
        "localhost.evil.example",
        "127.0.0.1.nip.io",
        "user@localhost",
        "localhost@evil.example",
        "evil.example@localhost:80",
        " localhost",
        "localhost :80",
        "local host",
        "::1",  # unbracketed IPv6 is not a valid Host
        "[::1",
        "[::1]x",
        "localhost:abc",
        "localhost:99999",
        "localhost/path",
        "0.0.0.0:8080",
        "192.168.1.10",
    ],
)
def test_is_allowed_local_host_rejects_other_hosts(host):
    assert is_allowed_local_host(host) is False


@pytest.mark.parametrize(
    ("origin", "host"),
    [
        (None, "localhost:8080"),
        ("", "localhost:8080"),
        ("http://localhost:8080", "localhost:8080"),
        ("HTTP://LOCALHOST:8080", "localhost:8080"),
        ("http://127.0.0.1:9000", "127.0.0.1:9000"),
        ("http://[::1]:8080", "[::1]:8080"),
        ("http://localhost", "localhost:80"),
        ("http://localhost:80", "localhost"),
        ("https://localhost:443", "localhost"),
    ],
)
def test_is_same_origin_accepts_matching_or_missing_origin(origin, host):
    assert is_same_origin(origin, host) is True


@pytest.mark.parametrize(
    ("origin", "host"),
    [
        ("null", "localhost:8080"),
        ("http://evil.example", "localhost:8080"),
        ("http://evil.example:8080", "localhost:8080"),
        ("http://localhost:8081", "localhost:8080"),
        ("http://127.0.0.1:8080", "localhost:8080"),
        ("https://localhost:8080", "localhost:80"),
        ("ftp://localhost:8080", "localhost:8080"),
        ("file://", "localhost:8080"),
        ("localhost:8080", "localhost:8080"),
        ("http://user@localhost:8080", "localhost:8080"),
        ("http://localhost:8080/path", "localhost:8080"),
        ("http://", "localhost:8080"),
        ("http://localhost:8080", None),
        ("http://[::1", "[::1]"),
    ],
)
def test_is_same_origin_rejects_mismatch(origin, host):
    assert is_same_origin(origin, host) is False


@pytest.mark.parametrize(
    ("content_type", "expected"),
    [
        ("application/json", True),
        ("application/json; charset=utf-8", True),
        ("Application/JSON ; charset=UTF-8", True),
        ("text/plain", False),
        ("text/plain; charset=utf-8", False),
        ("application/x-www-form-urlencoded", False),
        ("multipart/form-data; boundary=x", False),
        ("application/json-patch+json", False),
        ("", False),
        (None, False),
    ],
)
def test_is_json_content_type(content_type, expected):
    assert is_json_content_type(content_type) is expected


def test_has_custom_request_header_is_case_insensitive():
    assert has_custom_request_header({"X-PyGWalker-Request": "1"}) is True
    assert has_custom_request_header({"x-pygwalker-request": " 1 "}) is True
    assert has_custom_request_header({"X-PYGWALKER-REQUEST": "1"}) is True
    assert has_custom_request_header({"X-PyGWalker-Request": "0"}) is False
    assert has_custom_request_header({"X-PyGWalker-Request": ""}) is False
    assert has_custom_request_header({}) is False
    assert has_custom_request_header({"X-Requested-With": "1"}) is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", (0, None)),
        ("123", (123, None)),
        (" 42 ", (42, None)),
        (str(MAX_COMM_BODY_BYTES), (MAX_COMM_BODY_BYTES, None)),
        (str(MAX_COMM_BODY_BYTES + 1), (None, 413)),
        ("99999999999999999999", (None, 413)),
        (None, (None, 400)),
        ("", (None, 400)),
        ("-1", (None, 400)),
        ("+1", (None, 400)),
        ("1.5", (None, 400)),
        ("abc", (None, 400)),
        ("1, 2", (None, 400)),
        ("١٢", (None, 400)),  # non-ASCII digits
    ],
)
def test_parse_content_length(value, expected):
    assert parse_content_length(value) == expected


def test_parse_content_length_custom_limit():
    assert parse_content_length("11", max_bytes=10) == (None, 413)
    assert parse_content_length("10", max_bytes=10) == (10, None)


# =========================================================================================
# stdlib web server (pygwalker.api.webserver)
# =========================================================================================


class _WebWalker:
    gid = "web-gid"

    def __init__(self):
        self.comm = BaseCommunication(self.gid)
        self.ping_calls = 0
        self.envelopes = []
        self.comm.register("ping", self._ping)
        original = self.comm._receive_msg

        def _spy(action, data):
            self.envelopes.append({"action": action, "data": data})
            return original(action, data)

        self.comm._receive_msg = _spy

    def _ping(self, _data):
        self.ping_calls += 1
        return {}

    def _get_props(self, env):
        return {"env": env}

    def _get_render_iframe(self, props):
        return f"<html><body>PYGWALKER_PAGE {props['communicationUrl']}</body></html>"


@contextmanager
def _running_webserver(auto_shutdown=False):
    walker = _WebWalker()
    state = webserver._GlobalState(auto_shutdown=auto_shutdown)
    handler = webserver._create_handler_with_walker(walker, state)
    server = webserver.CustomTCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1], walker, state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _request(port, method, path, headers=None, body=None, host=None, content_length=True):
    """Send a request with full control over the Host / Content-Length headers."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        conn.putheader("Host", host if host is not None else f"localhost:{port}")
        for name, value in (headers or {}).items():
            conn.putheader(name, value)
        if body is not None and content_length:
            conn.putheader("Content-Length", str(len(body)))
        conn.endheaders(body)
        response = conn.getresponse()
        return response.status, response.headers, response.read()
    finally:
        conn.close()


def _login(port, state):
    status, headers, _ = _request(port, "GET", f"/?token={state.auth_token}")
    assert status == 302
    return headers


def _cookie_header(state):
    return {"Cookie": f"{webserver.AUTH_COOKIE_NAME}={state.auth_token}"}


def _post_comm(port, state, payload=PING, headers=None, path=None, **kwargs):
    merged = {**_cookie_header(state), **VALID_COMM_HEADERS, **(headers or {})}
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    return _request(port, "POST", path or f"/comm/{_WebWalker.gid}", headers=merged, body=body, **kwargs)


def test_webserver_state_has_random_per_server_token():
    first = webserver._GlobalState(auto_shutdown=False)
    second = webserver._GlobalState(auto_shutdown=False)

    assert len(first.auth_token) >= 32
    assert first.auth_token != second.auth_token


def test_webserver_happy_path_token_cookie_comm_and_health():
    with _running_webserver() as (port, walker, state):
        login_headers = _login(port, state)
        assert login_headers["Location"] == "/"
        assert login_headers["Cache-Control"] == "no-store"
        assert login_headers["Referrer-Policy"] == "no-referrer"
        set_cookie = login_headers["Set-Cookie"]
        assert set_cookie.startswith(f"{webserver.AUTH_COOKIE_NAME}={state.auth_token};")
        assert "HttpOnly" in set_cookie
        assert "SameSite=Strict" in set_cookie
        assert "Path=/" in set_cookie

        status, headers, body = _request(port, "GET", "/", headers=_cookie_header(state))
        assert status == 200
        assert headers["Content-Type"] == "text/html; charset=utf-8"
        assert headers["Cache-Control"] == "no-store"
        assert b"PYGWALKER_PAGE comm" in body

        status, headers, body = _post_comm(port, state)
        assert status == 200
        assert headers["Content-Type"] == "application/json; charset=utf-8"
        assert headers["Cache-Control"] == "no-store"
        assert json.loads(body) == {"code": 0, "data": {}, "message": "success"}
        assert walker.ping_calls == 1

        # The bare /comm path (used before the gid is known) and a same-origin Origin also work.
        status, _, _ = _post_comm(port, state, path="/comm", headers={"Origin": f"http://localhost:{port}"})
        assert status == 200
        assert walker.ping_calls == 2

        before = state.last_health_time
        status, headers, body = _request(port, "GET", "/health", headers=_cookie_header(state))
        assert status == 200
        assert body == b"OK"
        assert headers["Cache-Control"] == "no-store"
        assert state.last_health_time != before


def test_webserver_health_script_sends_credentials():
    assert 'credentials: "same-origin"' in webserver._SEND_HEALTH_JS_SCRIPT

    with _running_webserver(auto_shutdown=True) as (port, _walker, state):
        status, _, body = _request(port, "GET", "/", headers=_cookie_header(state))
        assert status == 200
        assert b'fetch("/health"' in body


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Cookie": f"{webserver.AUTH_COOKIE_NAME}=wrong"},
        {"Cookie": "other=1"},
        {"Cookie": "\x00garbage;;=="},
    ],
)
def test_webserver_index_requires_token_or_cookie(headers):
    with _running_webserver() as (port, walker, _state):
        status, resp_headers, body = _request(port, "GET", "/", headers=headers)
        assert status == 403
        assert "Set-Cookie" not in resp_headers
        assert b"PYGWALKER_PAGE" not in body
        assert walker.envelopes == []


def test_webserver_rejects_wrong_token():
    with _running_webserver() as (port, _walker, state):
        status, headers, body = _request(port, "GET", "/?token=not-the-token")
        assert status == 403
        assert "Set-Cookie" not in headers
        assert b"PYGWALKER_PAGE" not in body

        status, _, _ = _request(port, "GET", "/?token=")
        assert status == 403

        # The real token still works afterwards.
        _login(port, state)


def test_webserver_comm_requires_cookie():
    with _running_webserver() as (port, walker, _state):
        body = json.dumps(PING).encode("utf-8")
        status, _, _ = _request(port, "POST", f"/comm/{walker.gid}", headers=VALID_COMM_HEADERS, body=body)
        assert status == 403

        status, _, _ = _request(
            port,
            "POST",
            f"/comm/{walker.gid}",
            headers={**VALID_COMM_HEADERS, "Cookie": f"{webserver.AUTH_COOKIE_NAME}=wrong"},
            body=body,
        )
        assert status == 403
        assert walker.envelopes == []
        assert walker.ping_calls == 0


def test_webserver_health_requires_cookie():
    with _running_webserver() as (port, _walker, state):
        before = state.last_health_time
        status, _, _ = _request(port, "GET", "/health")
        assert status == 403
        assert state.last_health_time == before


@pytest.mark.parametrize("host", ["evil.example", "evil.example:8080", "localhost.evil.example", ""])
def test_webserver_rejects_bad_host_on_every_route(host):
    with _running_webserver() as (port, walker, state):
        status, headers, _ = _request(port, "GET", f"/?token={state.auth_token}", host=host)
        assert status == 403
        assert "Set-Cookie" not in headers

        status, _, _ = _request(port, "GET", "/", headers=_cookie_header(state), host=host)
        assert status == 403

        status, _, _ = _post_comm(port, state, host=host)
        assert status == 403
        assert walker.envelopes == []


@pytest.mark.parametrize("origin", ["http://evil.example", "null", "http://localhost:1"])
def test_webserver_rejects_cross_origin(origin):
    with _running_webserver() as (port, walker, state):
        status, _, _ = _post_comm(port, state, headers={"Origin": origin})
        assert status == 403

        status, headers, _ = _request(port, "GET", f"/?token={state.auth_token}", headers={"Origin": origin})
        assert status == 403
        assert "Set-Cookie" not in headers
        assert walker.envelopes == []


def test_webserver_checks_host_and_origin_before_method_dispatch():
    with _running_webserver() as (port, walker, state):
        before = state.last_health_time
        for method in ("HEAD", "PUT", "DELETE", "PATCH", "OPTIONS", "TRACE"):
            for headers in ({"host": "untrusted.invalid"}, {"headers": {"Origin": "null"}}):
                status, response_headers, _ = _request(port, method, "/health", **headers)
                assert status == 403
                assert "Set-Cookie" not in response_headers
        assert state.last_health_time == before
        assert walker.envelopes == []


def test_webserver_rejects_non_json_content_type():
    with _running_webserver() as (port, walker, state):
        status, _, _ = _post_comm(port, state, headers={"Content-Type": "text/plain"})
        assert status == 415

        status, _, _ = _post_comm(port, state, headers={"Content-Type": "application/x-www-form-urlencoded"})
        assert status == 415
        assert walker.envelopes == []


def test_webserver_rejects_missing_custom_header():
    with _running_webserver() as (port, walker, state):
        body = json.dumps(PING).encode("utf-8")
        status, _, _ = _request(
            port,
            "POST",
            f"/comm/{walker.gid}",
            headers={**_cookie_header(state), "Content-Type": "application/json"},
            body=body,
        )
        assert status == 403

        status, _, _ = _post_comm(port, state, headers={CUSTOM_REQUEST_HEADER: "0"})
        assert status == 403
        assert walker.envelopes == []


def test_webserver_does_not_serve_files():
    with _running_webserver() as (port, walker, state):
        for path in ("/pyproject.toml", "/README.md", "/../../etc/passwd", "/comm/../pyproject.toml"):
            status, _, body = _request(port, "GET", path, headers=_cookie_header(state))
            assert status == 404, path
            assert b"[project]" not in body

        status, _, body = _request(port, "HEAD", "/pyproject.toml", headers=_cookie_header(state))
        assert status == 405
        assert body == b""

        for method in ("PUT", "DELETE", "PATCH", "OPTIONS"):
            status, _, _ = _request(port, method, "/", headers=_cookie_header(state))
            assert status == 405, method
        assert walker.envelopes == []


def test_webserver_rejects_unknown_post_paths():
    with _running_webserver() as (port, walker, state):
        for path in ("/other", "/comm/other-gid", "/commx", "/comm/web-gid/extra"):
            status, _, _ = _post_comm(port, state, path=path)
            assert status == 404, path
        assert walker.envelopes == []


def test_webserver_rejects_missing_or_invalid_content_length():
    with _running_webserver() as (port, walker, state):
        status, _, _ = _post_comm(port, state, content_length=False)
        assert status == 400

        for value in ("abc", "-1", "1.5"):
            status, _, _ = _post_comm(port, state, headers={"Content-Length": value}, content_length=False)
            assert status == 400, value
        assert walker.envelopes == []


def test_webserver_rejects_oversized_content_length_without_reading_body():
    with _running_webserver() as (port, walker, state):
        status, _, _ = _request(
            port,
            "POST",
            f"/comm/{walker.gid}",
            headers={
                **_cookie_header(state),
                **VALID_COMM_HEADERS,
                "Content-Length": str(MAX_COMM_BODY_BYTES + 1),
            },
            body=b"",
            content_length=False,
        )
        assert status == 413
        assert walker.envelopes == []


def test_webserver_rejects_invalid_json_body():
    with _running_webserver() as (port, walker, state):
        status, _, body = _post_comm(port, state, payload=b"{not json")
        assert status == 400
        assert json.loads(body)["success"] is False

        status, _, _ = _post_comm(port, state, payload=b"\xff\xfe")
        assert status == 400
        assert walker.envelopes == []


def test_webserver_rejects_invalid_envelopes_before_dispatch():
    with _running_webserver() as (port, walker, state):
        for payload in (None, [], {}, {"action": 42}):
            status, _, _ = _post_comm(port, state, payload=payload)
            assert status == 400
        assert walker.envelopes == []
        status, _, _ = _post_comm(port, state, payload={"action": "ping"})
        assert status == 200
        assert walker.envelopes == [PING]


def test_webserver_server_is_threaded():
    assert issubclass(webserver.CustomTCPServer, webserver.socketserver.ThreadingMixIn)
    assert webserver.CustomTCPServer.daemon_threads is True
    assert webserver.CustomTCPServer.allow_reuse_address == (sys.platform != "win32")
    assert webserver._PygWalkerHandler.timeout == 30
    assert issubclass(webserver._PygWalkerHandler, webserver.http.server.BaseHTTPRequestHandler)
    assert not issubclass(webserver._PygWalkerHandler, webserver.http.server.SimpleHTTPRequestHandler)


def test_webserver_slow_client_does_not_block_other_requests():
    with _running_webserver() as (port, _walker, state):
        stalled = socket.create_connection(("127.0.0.1", port), timeout=5)
        try:
            stalled.sendall(b"GET /health HTTP/1.1\r\n")  # never finishes its headers
            status, _, _ = _request(port, "GET", "/health", headers=_cookie_header(state))
            assert status == 200
        finally:
            stalled.close()


def test_start_server_prints_tokenized_url_and_closes_parser(monkeypatch, capsys):
    closed = []

    class FakeServer:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def serve_forever(self):
            return None

    class FakeParser:
        def close(self):
            closed.append(True)

    class FakeWalker:
        gid = "start-gid"
        use_preview = True
        data_parser = FakeParser()

        def _init_callback(self, comm, preview_tool=None):
            self.comm = comm

    monkeypatch.setattr(webserver, "CustomTCPServer", FakeServer)
    webserver._start_server(FakeWalker(), 8770, auto_open=False, auto_shutdown=False)

    output = capsys.readouterr().out
    assert "http://localhost:8770/?token=" in output
    assert closed == [True]


# =========================================================================================
# Web-framework transports (Streamlit / Gradio / Reflex)
# =========================================================================================


class _SpyComm(BaseCommunication):
    def __init__(self, gid):
        super().__init__(gid)
        self.envelopes = []
        self.register("ping", lambda _data: {})

    def _receive_msg(self, action, data):
        self.envelopes.append({"action": action, "data": data})
        return super()._receive_msg(action, data)


def _starlette_client(route_path, endpoint):
    pytest.importorskip("httpx")
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.testclient import TestClient

    return TestClient(Starlette(routes=[Route(route_path, endpoint, methods=["POST"])]))


def _assert_framework_transport(client, url, comm):
    body = json.dumps(PING)

    response = client.post(url, content=body, headers={"Content-Type": "text/plain", CUSTOM_REQUEST_HEADER: "1"})
    assert response.status_code == 415

    response = client.post(url, content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 403

    response = client.post(
        url,
        content="x" * (MAX_COMM_BODY_BYTES + 1),
        headers=VALID_COMM_HEADERS,
    )
    assert response.status_code == 413

    response = client.post(url, content="{not json", headers=VALID_COMM_HEADERS)
    assert response.status_code == 400
    assert "not json" not in response.text
    for payload in (None, [], {}, {"action": 42}):
        response = client.post(url, content=json.dumps(payload), headers=VALID_COMM_HEADERS)
        assert response.status_code == 400
    assert comm.envelopes == []

    response = client.post(url, content=json.dumps({"action": "ping"}), headers=VALID_COMM_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"code": 0, "data": {}, "message": "success"}
    assert comm.envelopes == [PING]


def test_gradio_router_enforces_http_checks():
    pytest.importorskip("starlette")
    from pygwalker.communications import gradio_comm

    comm = _SpyComm("gradio-http")
    gradio_comm.gradio_comm_map["gradio-http"] = comm
    try:
        client = _starlette_client("/_pygwalker/comm/{gid}", gradio_comm._pygwalker_router)
        _assert_framework_transport(client, "/_pygwalker/comm/gradio-http", comm)
    finally:
        gradio_comm.gradio_comm_map.pop("gradio-http", None)


def test_reflex_endpoint_enforces_http_checks():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from starlette.testclient import TestClient

    from pygwalker.communications import reflex_comm

    comm = _SpyComm("reflex-http")
    reflex_comm.reflex_comm_map["reflex-http"] = comm
    try:
        client = TestClient(reflex_comm._create_pygwalker_app())
        _assert_framework_transport(client, "/reflex-http", comm)
    finally:
        reflex_comm.reflex_comm_map.pop("reflex-http", None)


def test_reflex_legacy_router_enforces_http_checks():
    pytest.importorskip("starlette")
    pytest.importorskip("fastapi")
    from pygwalker.communications import reflex_comm

    comm = _SpyComm("reflex-legacy")
    reflex_comm.reflex_comm_map["reflex-legacy"] = comm
    try:
        client = _starlette_client("/_pygwalker/comm/{gid}", reflex_comm._pygwalker_router)
        _assert_framework_transport(client, "/_pygwalker/comm/reflex-legacy", comm)
    finally:
        reflex_comm.reflex_comm_map.pop("reflex-legacy", None)


@pytest.mark.parametrize("legacy", [False, True])
def test_reflex_endpoint_hides_internal_errors(legacy):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from starlette.testclient import TestClient

    from pygwalker.communications import reflex_comm

    class _ExplodingComm(BaseCommunication):
        def _receive_msg(self, action, data):
            raise RuntimeError("SECRET_VALUE leaked")

    reflex_comm.reflex_comm_map["reflex-boom"] = _ExplodingComm("reflex-boom")
    try:
        if legacy:
            client = _starlette_client("/{gid}", reflex_comm._pygwalker_router)
        else:
            client = TestClient(reflex_comm._create_pygwalker_app())
        response = client.post("/reflex-boom", content=json.dumps(PING), headers=VALID_COMM_HEADERS)
    finally:
        reflex_comm.reflex_comm_map.pop("reflex-boom", None)

    assert response.status_code == 500
    assert "SECRET_VALUE" not in response.text


def _streamlit_comm_module():
    pytest.importorskip("streamlit")
    pytest.importorskip("tornado")
    return importlib.import_module("pygwalker.communications.streamlit_comm")


def test_streamlit_tornado_handler_enforces_http_checks():
    streamlit_comm = _streamlit_comm_module()
    import tornado.httpclient
    import tornado.httpserver
    import tornado.netutil
    import tornado.web

    comm = _SpyComm("streamlit-tornado")
    streamlit_comm.streamlit_comm_map["streamlit-tornado"] = comm

    async def _exercise():
        app = tornado.web.Application([(r"/_stcore/_pygwalker/comm/(.+)", streamlit_comm.PygwalkerHandler)])
        sockets = tornado.netutil.bind_sockets(0, "127.0.0.1")
        port = sockets[0].getsockname()[1]
        server = tornado.httpserver.HTTPServer(app)
        server.add_sockets(sockets)
        client = tornado.httpclient.AsyncHTTPClient()
        url = f"http://127.0.0.1:{port}/_stcore/_pygwalker/comm/streamlit-tornado"
        body = json.dumps(PING)

        async def _post(headers, payload=body):
            response = await client.fetch(url, method="POST", headers=headers, body=payload, raise_error=False)
            return response.code, response.body

        try:
            results = {
                "text_plain": await _post({"Content-Type": "text/plain", CUSTOM_REQUEST_HEADER: "1"}),
                "no_header": await _post({"Content-Type": "application/json"}),
                "bad_envelopes": [
                    await _post(VALID_COMM_HEADERS, json.dumps(payload)) for payload in (None, [], {}, {"action": 42})
                ],
                "bad_json": await _post(VALID_COMM_HEADERS, "{not json"),
                "oversized": await _post(VALID_COMM_HEADERS, "x" * (MAX_COMM_BODY_BYTES + 1)),
                "rejected_envelopes": list(comm.envelopes),
                "ok": await _post(VALID_COMM_HEADERS, json.dumps({"action": "ping"})),
            }
        finally:
            server.stop()
            await server.close_all_connections()
        return results

    try:
        results = asyncio.run(_exercise())
    finally:
        streamlit_comm.streamlit_comm_map.pop("streamlit-tornado", None)

    assert results["text_plain"][0] == 415
    assert results["no_header"][0] == 403
    assert all(status == 400 for status, _ in results["bad_envelopes"])
    assert results["bad_json"][0] == 400
    assert results["oversized"][0] == 413
    assert results["rejected_envelopes"] == []
    assert results["ok"][0] == 200
    assert json.loads(results["ok"][1]) == {"code": 0, "data": {}, "message": "success"}
    assert comm.envelopes == [PING]
