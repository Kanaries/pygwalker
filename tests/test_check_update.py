from pygwalker.services import check_update
from pygwalker.services.global_var import GlobalVarManager


def test_check_update_starts_daemon_thread(monkeypatch):
    started_threads = []
    previous_privacy = GlobalVarManager.privacy
    GlobalVarManager.privacy = "events"

    class FakeThread:
        def __init__(self, *, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            started_threads.append(self)

    monkeypatch.setattr(check_update, "Thread", FakeThread)

    try:
        check_update.check_update()
    finally:
        GlobalVarManager.privacy = previous_privacy

    assert len(started_threads) == 1
    assert started_threads[0].target is check_update._check_update
    assert started_threads[0].daemon is True


def test_check_update_starts_thread_in_update_only_mode(monkeypatch):
    started_threads = []
    previous_privacy = GlobalVarManager.privacy
    GlobalVarManager.privacy = "update-only"

    class FakeThread:
        def __init__(self, *, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            started_threads.append(self)

    monkeypatch.setattr(check_update, "Thread", FakeThread)

    try:
        check_update.check_update()
    finally:
        GlobalVarManager.privacy = previous_privacy

    assert len(started_threads) == 1
    assert started_threads[0].target is check_update._check_update
    assert started_threads[0].daemon is True


def test_check_update_does_not_start_thread_in_offline_mode(monkeypatch):
    started_threads = []
    previous_privacy = GlobalVarManager.privacy
    GlobalVarManager.privacy = "offline"

    class FakeThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            started_threads.append(self)

    monkeypatch.setattr(check_update, "Thread", FakeThread)

    try:
        check_update.check_update()
    finally:
        GlobalVarManager.privacy = previous_privacy

    assert started_threads == []
