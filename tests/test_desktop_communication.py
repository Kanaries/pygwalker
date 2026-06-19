from types import SimpleNamespace

from pygwalker.communications.protocol import OpenDesktopRequest
from pygwalker.services.desktop_communication import DesktopCommunicationService


def test_desktop_communication_imports_current_records():
    import_calls = []
    desktop_import = SimpleNamespace(import_to_desktop=lambda **kwargs: import_calls.append(kwargs))
    walker = SimpleNamespace(
        data_parser=SimpleNamespace(to_records=lambda: [{"city": "London"}, {"city": "Tokyo"}]),
    )

    response = DesktopCommunicationService(walker, desktop_import).open_in_desktop(
        OpenDesktopRequest(spec=[{"name": "Chart"}], fields=[{"fid": "city"}])
    )

    assert response == {}
    assert import_calls == [
        {
            "spec": [{"name": "Chart"}],
            "fields": [{"fid": "city"}],
            "records": [{"city": "London"}, {"city": "Tokyo"}],
        }
    ]
