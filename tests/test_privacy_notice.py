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
    monkeypatch.setattr(track.analytics, "track", lambda **kwargs: analytics_calls.append(kwargs))
    monkeypatch.setattr(track.kanaries_track, "track", lambda payload: kanaries_calls.append(payload))

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
    monkeypatch.setattr(track.analytics, "track", lambda **kwargs: analytics_calls.append(kwargs))

    try:
        track.track_event("invoke_props", {"mode": "test"})
    finally:
        GlobalVarManager.privacy = previous_privacy

    assert capsys.readouterr().out == ""
    assert notice_calls == []
    assert analytics_calls == []
