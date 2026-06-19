from pygwalker.services import preview_image


def test_preview_image_tool_renders_on_daemon_thread(monkeypatch):
    started_threads = []
    display_calls = []

    class FakeThread:
        def __init__(self, *, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            started_threads.append(self)

    monkeypatch.setattr(preview_image, "Thread", FakeThread)
    monkeypatch.setattr(preview_image, "JupyterFrontEnd", lambda: None)
    monkeypatch.setattr(preview_image, "display_html", lambda html, slot_id: display_calls.append((html, slot_id)))

    tool = preview_image.PreviewImageTool("preview")
    tool.async_render_gw_review("<div>chart</div>")
    tool.async_render_gw_review("<div>chart 2</div>")

    assert len(started_threads) == 1
    assert started_threads[0].daemon is True
    tool._render_next_preview()
    tool._render_next_preview()
    assert display_calls == [
        ("<div>chart</div>", "pygwalker-preview-preview"),
        ("<div>chart 2</div>", "pygwalker-preview-preview"),
    ]


def test_preview_image_tool_keeps_worker_alive_after_render_error(monkeypatch):
    display_calls = []

    class FakeThread:
        def __init__(self, *, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            pass

    def fake_display_html(html, slot_id):
        if html == "<div>bad chart</div>":
            raise RuntimeError("render failed")
        display_calls.append((html, slot_id))

    monkeypatch.setattr(preview_image, "Thread", FakeThread)
    monkeypatch.setattr(preview_image, "JupyterFrontEnd", lambda: None)
    monkeypatch.setattr(preview_image, "display_html", fake_display_html)

    tool = preview_image.PreviewImageTool("preview")
    tool.async_render_gw_review("<div>bad chart</div>")
    tool.async_render_gw_review("<div>good chart</div>")

    tool._safe_render_next_preview()
    tool._safe_render_next_preview()

    assert display_calls == [("<div>good chart</div>", "pygwalker-preview-preview")]
