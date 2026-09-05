import json
import subprocess
import sys

import pandas as pd
import pytest

from pygwalker.jupyter_extension import (
    COMM_TARGET,
    JupyterExtensionSession,
    discover_dataframes,
    ensure_registered,
    resolve_dataframe,
)


class FakeComm:
    def __init__(self):
        self.callback = None
        self.sent = []

    def on_msg(self, callback):
        self.callback = callback

    def send(self, data):
        self.sent.append(data)

    def request(self, action, data=None, rid="request-id"):
        self.callback(
            {
                "content": {
                    "data": {
                        "type": "pyg_request",
                        "msg": {
                            "gid": "extension",
                            "rid": rid,
                            "action": action,
                            "data": data or {},
                        },
                    }
                }
            }
        )
        envelope = json.loads(self.sent[-1]["data"])
        assert envelope["action"] == "finish_request"
        assert envelope["rid"] == rid
        return envelope["data"]


class FakeCoreWalker:
    def __init__(self, dataset):
        self.dataset = dataset
        self.gid = "walker-session"
        self.callback_communications = []

    def _init_callback(self, communication):
        self.callback_communications.append(communication)
        communication.register("ping", lambda _: {"data": "pong"})

    def _get_props(self, env):
        return {"id": self.gid, "env": env, "dataSource": []}


class FakePublicWalker:
    instances = []

    def __init__(self, dataset, **kwargs):
        self.dataset = dataset
        self.kwargs = kwargs
        self.core = FakeCoreWalker(dataset)
        self.instances.append(self)


def test_discover_dataframes_returns_only_safe_top_level_pandas_names():
    namespace = {
        "z_frame": pd.DataFrame({"x": [1, 2]}),
        "A_frame": pd.DataFrame({"y": [3]}),
        "_private": pd.DataFrame({"x": []}),
        "not-a-name": pd.DataFrame({"x": []}),
        "plain": [1, 2, 3],
    }

    assert discover_dataframes(namespace) == [
        {"name": "A_frame", "rows": 1, "columns": 1},
        {"name": "z_frame", "rows": 2, "columns": 1},
    ]


def test_resolve_dataframe_requires_a_discovered_name_and_rechecks_type():
    frame = pd.DataFrame({"x": [1]})
    namespace = {"frame": frame, "other": frame}

    assert resolve_dataframe(namespace, "frame", {"frame"}) is frame
    with pytest.raises(ValueError, match="Refresh the sidebar"):
        resolve_dataframe(namespace, "other", {"frame"})

    namespace["frame"] = "now stale"
    with pytest.raises(ValueError, match="no longer"):
        resolve_dataframe(namespace, "frame", {"frame"})


def test_session_lists_opens_and_replaces_a_real_protocol_session():
    FakePublicWalker.instances = []
    first = pd.DataFrame({"x": [1]})
    second = pd.DataFrame({"y": [2, 3]})
    comm = FakeComm()
    JupyterExtensionSession(
        comm,
        {"first": first, "second": second},
        walker_factory=FakePublicWalker,
    )

    handshake = comm.request("extension_handshake")
    assert handshake["code"] == 0
    assert handshake["data"]["protocolVersion"] == 1
    assert "kernel-computation" in handshake["data"]["capabilities"]

    listed = comm.request("list_dataframes")
    assert listed["code"] == 0
    assert [item["name"] for item in listed["data"]["dataframes"]] == ["first", "second"]

    opened = comm.request("open_dataframe", {"name": "first"})
    assert opened["code"] == 0
    assert opened["data"]["props"]["env"] == "jupyter_extension"
    assert FakePublicWalker.instances[-1].dataset is first
    assert FakePublicWalker.instances[-1].kwargs["computation"] == "kernel"

    comm.request("open_dataframe", {"name": "second"})
    assert len(FakePublicWalker.instances) == 2
    assert FakePublicWalker.instances[-1].dataset is second

    ping = comm.request("ping")
    assert ping["code"] == 0
    assert ping["data"] == {"data": "pong"}


def test_session_rejects_stale_and_unlisted_names_over_the_protocol():
    namespace = {"frame": pd.DataFrame({"x": [1]})}
    comm = FakeComm()
    JupyterExtensionSession(comm, namespace, walker_factory=FakePublicWalker)

    not_listed = comm.request("open_dataframe", {"name": "frame"})
    assert not_listed["code"] != 0
    assert "Refresh the sidebar" in not_listed["message"]

    comm.request("list_dataframes")
    namespace["frame"] = None
    stale = comm.request("open_dataframe", {"name": "frame"})
    assert stale["code"] != 0
    assert "no longer" in stale["message"]


def test_real_extension_session_opens_without_offering_unsupported_save(monkeypatch):
    from pygwalker.services.global_var import GlobalVarManager

    monkeypatch.setattr(GlobalVarManager, "privacy", "offline")
    comm = FakeComm()
    JupyterExtensionSession(comm, {"frame": pd.DataFrame({"x": [1, 2]})})
    comm.request("list_dataframes")
    opened = comm.request("open_dataframe", {"name": "frame"})

    assert opened["code"] == 0, opened
    assert opened["data"]["props"]["useSaveTool"] is False
    assert opened["data"]["props"]["useKernelCalc"] is True
    assert comm.request("get_latest_vis_spec")["code"] == 0
    for action in ("update_spec", "save_chart"):
        response = comm.request(action)
        assert response["code"] != 0
        assert response["message"] == f"Unknown action: {action}"


def test_ensure_registered_is_idempotent():
    class FakeManager:
        def __init__(self):
            self.targets = []

        def register_target(self, name, callback):
            self.targets.append((name, callback))

    class FakeKernel:
        def __init__(self):
            self.comm_manager = FakeManager()

    class FakeIPython:
        def __init__(self):
            self.kernel = FakeKernel()
            self.user_ns = {}

    ipython = FakeIPython()
    first = ensure_registered(ipython)
    second = ensure_registered(ipython)

    assert first == second
    assert first["target"] == COMM_TARGET
    assert len(ipython.kernel.comm_manager.targets) == 1


def test_importing_core_does_not_activate_the_extension_bridge():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import pygwalker; assert 'pygwalker.jupyter_extension' not in sys.modules",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
