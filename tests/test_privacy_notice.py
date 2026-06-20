import subprocess
import sys
from types import SimpleNamespace

from pygwalker.services import config, track
from pygwalker.services.global_var import GlobalVarManager


def test_default_privacy_is_update_only():
    assert config.DEFAULT_CONFIG["privacy"] == "update-only"
    assert config.privacy_item.default == "update-only"


def test_privacy_notice_sentinel_is_written_once(monkeypatch, tmp_path):
    notice_path = tmp_path / "privacy_notice_shown"
    monkeypatch.setattr(config, "PRIVACY_NOTICE_PATH", str(notice_path))

    assert config.should_show_privacy_notice() is True
    assert notice_path.read_text() == "shown"
    assert config.should_show_privacy_notice() is False


def test_track_event_prints_privacy_notice_once_and_handles_empty_properties(monkeypatch, capsys):
    analytics_calls = []
    kanaries_calls = []
    previous_privacy = GlobalVarManager.privacy
    GlobalVarManager.privacy = "events"

    monkeypatch.setattr(track, "should_show_privacy_notice", lambda: True)
    monkeypatch.setattr(track, "get_local_user_id", lambda: "test-user")
    monkeypatch.setattr(
        track,
        "_get_analytics_client",
        lambda: SimpleNamespace(track=lambda **kwargs: analytics_calls.append(kwargs)),
    )
    monkeypatch.setattr(
        track,
        "_get_kanaries_track_client",
        lambda: SimpleNamespace(track=lambda payload: kanaries_calls.append(payload)),
    )

    try:
        track.track_event("invoke_props")
    finally:
        GlobalVarManager.privacy = previous_privacy

    assert "pygwalker config --set privacy=update-only" in capsys.readouterr().out
    assert analytics_calls == [{"user_id": "test-user", "event": "invoke_props", "properties": {}}]
    assert kanaries_calls == [{"user_id": "test-user"}]


def test_track_event_does_not_emit_when_privacy_is_not_events(monkeypatch, capsys):
    notice_calls = []
    analytics_calls = []
    previous_privacy = GlobalVarManager.privacy
    GlobalVarManager.privacy = "update-only"

    monkeypatch.setattr(track, "should_show_privacy_notice", lambda: notice_calls.append(True) or True)
    monkeypatch.setattr(
        track,
        "_get_analytics_client",
        lambda: SimpleNamespace(track=lambda **kwargs: analytics_calls.append(kwargs)),
    )

    try:
        track.track_event("invoke_props", {"mode": "test"})
    finally:
        GlobalVarManager.privacy = previous_privacy

    assert capsys.readouterr().out == ""
    assert notice_calls == []
    assert analytics_calls == []


def test_track_event_does_not_import_analytics_clients_when_privacy_is_not_events():
    code = """
import builtins

original_import = builtins.__import__

def blocked_import(name, *args, **kwargs):
    if name == "kanaries_track" or name == "segment" or name.startswith("segment."):
        raise AssertionError(f"unexpected analytics import: {name}")
    return original_import(name, *args, **kwargs)

builtins.__import__ = blocked_import

from pygwalker.services.global_var import GlobalVarManager
from pygwalker.services.track import track_event

GlobalVarManager.privacy = "update-only"
track_event("invoke_props", {"mode": "test"})
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr


def test_analytics_clients_are_configured_without_background_workers(monkeypatch):
    fake_analytics = SimpleNamespace(
        write_key=None,
        sync_mode=False,
        timeout=15,
        max_retries=10,
        track=lambda **_kwargs: None,
    )
    fake_kanaries_track = SimpleNamespace(
        config=SimpleNamespace(
            auth_token=None,
            proxies=None,
            sync_send=False,
            timeout=15,
            max_retries=5,
            thread=1,
        ),
        track=lambda _payload: None,
    )

    previous_analytics_client = track._analytics_client
    previous_kanaries_track_client = track._kanaries_track_client
    monkeypatch.setitem(sys.modules, "segment", SimpleNamespace(analytics=fake_analytics))
    monkeypatch.setitem(sys.modules, "segment.analytics", fake_analytics)
    monkeypatch.setitem(sys.modules, "kanaries_track", fake_kanaries_track)
    track._analytics_client = None
    track._kanaries_track_client = None

    try:
        assert track._get_analytics_client() is fake_analytics
        assert track._get_kanaries_track_client() is fake_kanaries_track
    finally:
        track._analytics_client = previous_analytics_client
        track._kanaries_track_client = previous_kanaries_track_client

    assert fake_analytics.sync_mode is True
    assert fake_analytics.timeout == 1
    assert fake_analytics.max_retries == 0
    assert fake_kanaries_track.config.sync_send is True
    assert fake_kanaries_track.config.timeout == 1
    assert fake_kanaries_track.config.max_retries == 1
    assert fake_kanaries_track.config.thread == 0


def test_kanaries_track_single_retry_setting_does_not_loop(monkeypatch):
    from kanaries_track.request import RequestClient

    calls = []
    client = RequestClient(
        host="https://example.invalid",
        auth_token="test-token",
        max_retries=1,
        timeout=1,
        verify=True,
        proxy={},
    )

    def fail_post(*_args, **_kwargs):
        calls.append(True)
        raise OSError("network unavailable")

    monkeypatch.setattr(client.session, "post", fail_post)

    client.track([{"event": "test"}])

    assert calls == [True]
