"""Shared HTTP hardening helpers for PyGWalker's HTTP communication transports.

These helpers are intentionally pure (no framework imports) so they can be reused by the
stdlib web server, Streamlit (Tornado / Starlette), Gradio and Reflex transports.
"""

from collections import OrderedDict
from typing import Any, Dict, Mapping, Optional, Tuple
import json
import logging
import urllib.parse

logger = logging.getLogger(__name__)

CUSTOM_REQUEST_HEADER = "X-PyGWalker-Request"
CUSTOM_REQUEST_HEADER_VALUE = "1"
MAX_COMM_BODY_BYTES = 10 * 1024 * 1024  # 10 MiB
LOCALHOST_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "::1"})
DEFAULT_COMM_MAP_MAXSIZE = 256

_DEFAULT_PORTS = {"http": 80, "https": 443}


def _split_host_port(host: str) -> Optional[Tuple[str, Optional[int]]]:
    """Split an HTTP ``Host`` value into ``(hostname, port)``; ``None`` when malformed."""
    if not host or host != host.strip() or any(ch.isspace() for ch in host):
        return None
    if "@" in host or "/" in host or "\\" in host or "?" in host or "#" in host:
        return None

    if host.startswith("["):
        end = host.find("]")
        if end == -1:
            return None
        hostname = host[1:end]
        rest = host[end + 1 :]
        if not hostname:
            return None
        if rest == "":
            return hostname.lower(), None
        if not rest.startswith(":"):
            return None
        port_str = rest[1:]
    else:
        if host.count(":") > 1:
            # Bare (unbracketed) IPv6 literals are not valid in a Host header.
            return None
        hostname, sep, port_str = host.partition(":")
        if not hostname:
            return None
        if not sep:
            return hostname.lower(), None

    if not port_str.isdigit() or not port_str.isascii():
        return None
    port = int(port_str)
    if port < 0 or port > 65535:
        return None
    return hostname.lower(), port


def is_allowed_local_host(host_header: Optional[str]) -> bool:
    """Return True when the ``Host`` header names a loopback hostname (any port).

    Ports are deliberately not restricted so SSH port forwarding and Docker port mapping keep
    working. This defeats DNS-rebinding attacks, which carry the attacker's hostname.
    """
    if host_header is None:
        return False
    parsed = _split_host_port(host_header)
    if parsed is None:
        return False
    hostname, _ = parsed
    return hostname in LOCALHOST_HOSTNAMES


def _normalize_netloc(scheme: str, netloc: str) -> Optional[str]:
    parsed = _split_host_port(netloc)
    if parsed is None:
        return None
    hostname, port = parsed
    if port is not None and port == _DEFAULT_PORTS.get(scheme):
        port = None
    host_part = f"[{hostname}]" if ":" in hostname else hostname
    return host_part if port is None else f"{host_part}:{port}"


def is_same_origin(origin_header: Optional[str], host_header: Optional[str]) -> bool:
    """Return True when ``Origin`` is absent or matches the request ``Host``.

    Browsers always send ``Origin`` for cross-origin requests and for same-origin POSTs; a
    missing header therefore indicates a non-browser client or a same-origin navigation.
    """
    if origin_header is None or origin_header.strip() == "":
        return True
    if host_header is None or host_header.strip() == "":
        return False

    origin = origin_header.strip()
    if origin.lower() == "null":
        return False
    try:
        parsed = urllib.parse.urlsplit(origin)
    except ValueError:
        return False

    scheme = parsed.scheme.lower()
    if scheme not in _DEFAULT_PORTS:
        return False
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        return False
    if not parsed.netloc:
        return False

    origin_netloc = _normalize_netloc(scheme, parsed.netloc)
    host_netloc = _normalize_netloc(scheme, host_header.strip())
    if origin_netloc is None or host_netloc is None:
        return False
    return origin_netloc == host_netloc


def is_json_content_type(content_type: Optional[str]) -> bool:
    """Return True when the media type (ignoring parameters) is ``application/json``."""
    if not content_type:
        return False
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type == "application/json"


def get_header(headers: Optional[Mapping[str, str]], name: str) -> Optional[str]:
    """Case-insensitive header lookup that works for plain dicts and framework header objects."""
    if headers is None:
        return None
    getter = getattr(headers, "get", None)
    value = getter(name) if getter is not None else None
    if value is None:
        target = name.lower()
        try:
            items = headers.items()
        except AttributeError:
            return None
        for key, item_value in items:
            if isinstance(key, bytes):
                key = key.decode("latin-1")
            if str(key).lower() == target:
                value = item_value
                break
    if isinstance(value, bytes):
        value = value.decode("latin-1")
    return None if value is None else str(value)


def has_custom_request_header(headers: Mapping[str, str]) -> bool:
    """Return True when the ``X-PyGWalker-Request: 1`` header is present (case-insensitive name)."""
    value = get_header(headers, CUSTOM_REQUEST_HEADER)
    return value is not None and value.strip() == CUSTOM_REQUEST_HEADER_VALUE


def parse_content_length(
    value: Optional[str],
    max_bytes: int = MAX_COMM_BODY_BYTES,
) -> Tuple[Optional[int], Optional[int]]:
    """Parse a ``Content-Length`` header.

    Returns ``(length, None)`` when valid, ``(None, 400)`` when missing/malformed/negative and
    ``(None, 413)`` when larger than ``max_bytes``.
    """
    if value is None:
        return None, 400
    text = str(value).strip()
    if not text or not text.isascii() or not text.isdigit():
        return None, 400
    length = int(text)
    if length > max_bytes:
        return None, 413
    return length, None


class CommRequestError(Exception):
    """A rejected comm HTTP request; ``status`` is the HTTP status code to return."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message

    def to_payload(self) -> Dict[str, Any]:
        return {"success": False, "message": self.message}


def check_comm_request_headers(headers: Mapping[str, str]) -> None:
    """Validate the CSRF-relevant headers of a comm POST; raise ``CommRequestError`` if invalid.

    Requiring ``Content-Type: application/json`` plus the custom ``X-PyGWalker-Request`` header
    turns every cross-origin request into a CORS-preflighted one, which the comm routes never
    approve, so a hostile page cannot drive the comm channel through the user's browser.
    """
    if not is_json_content_type(get_header(headers, "Content-Type")):
        raise CommRequestError(415, "Content-Type must be application/json")
    if not has_custom_request_header(headers):
        raise CommRequestError(403, f"Missing {CUSTOM_REQUEST_HEADER} header")
    content_length = get_header(headers, "Content-Length")
    if content_length is not None:
        _, status = parse_content_length(content_length)
        if status == 413:
            raise CommRequestError(413, "Request body too large")
        if status is not None:
            raise CommRequestError(400, "Invalid Content-Length header")


def parse_json_body(body: bytes, max_bytes: int = MAX_COMM_BODY_BYTES) -> Any:
    """Decode a JSON request body, raising ``CommRequestError`` (400/413) on failure."""
    if len(body) > max_bytes:
        raise CommRequestError(413, "Request body too large")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise CommRequestError(400, "Invalid JSON in request body") from None


async def read_starlette_json(request: Any, max_bytes: int = MAX_COMM_BODY_BYTES) -> Any:
    """Validate and read the JSON body of a Starlette request with a hard size limit."""
    check_comm_request_headers(request.headers)
    stream = getattr(request, "stream", None)
    if stream is None:
        return parse_json_body(await request.body(), max_bytes)
    body = bytearray()
    async for chunk in stream():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise CommRequestError(413, "Request body too large")
    return parse_json_body(bytes(body), max_bytes)


def _close_comm(comm: Any) -> None:
    close = getattr(comm, "close", None)
    if not callable(close):
        return
    try:
        close()
    except Exception:  # pragma: no cover - defensive; cleanup must never break routing.
        logger.exception("Failed to close evicted PyGWalker communication")


class BoundedCommMap(OrderedDict):
    """A small LRU-ish ``gid -> comm`` registry that closes comms it drops.

    Overwriting a gid with a different comm, or evicting the oldest entry once ``maxsize`` is
    exceeded, calls ``close()`` on the dropped comm so its data parser can release resources.
    """

    def __init__(self, maxsize: int = DEFAULT_COMM_MAP_MAXSIZE):
        super().__init__()
        self.maxsize = maxsize

    def __setitem__(self, key, value) -> None:
        old = OrderedDict.get(self, key)
        if key in self:
            OrderedDict.__delitem__(self, key)
        OrderedDict.__setitem__(self, key, value)
        if old is not None and old is not value:
            _close_comm(old)
        while len(self) > self.maxsize:
            _, evicted = self.popitem(last=False)
            if evicted is not value:
                _close_comm(evicted)
