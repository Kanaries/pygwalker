import base64
import datetime as dt
import json
import urllib.parse
import zlib

from pygwalker.services.desktop_import import DesktopImportService


def _decode_query_value(link: str, name: str):
    parsed = urllib.parse.urlparse(link)
    query = urllib.parse.parse_qs(parsed.query)
    compressed = base64.b64decode(urllib.parse.unquote(query[name][0]))
    return json.loads(zlib.decompress(compressed).decode())


def test_desktop_import_service_builds_import_link():
    service = DesktopImportService(open_link=lambda _link: None)

    link = service.build_import_link(
        spec=[{"name": "Chart"}],
        fields=[{"fid": "city"}],
        records=[{"city": "London", "date": dt.date(2024, 1, 1)}],
    )

    parsed = urllib.parse.urlparse(link)
    assert parsed.scheme == "gw"
    assert parsed.netloc == "import"
    assert _decode_query_value(link, "spec") == [{"name": "Chart"}]
    assert _decode_query_value(link, "fields") == [{"fid": "city"}]
    assert _decode_query_value(link, "data") == [{"city": "London", "date": "2024-01-01"}]


def test_desktop_import_service_opens_built_link():
    links = []
    service = DesktopImportService(open_link=links.append)

    service.import_to_desktop(spec=[], fields=[], records=[])

    assert len(links) == 1
    assert urllib.parse.urlparse(links[0]).scheme == "gw"
