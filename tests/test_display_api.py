from types import SimpleNamespace

import pytest

from pygwalker.api import jupyter, webserver


@pytest.fixture(params=[(jupyter, "render"), (jupyter, "table"), (webserver, "render"), (webserver, "table")])
def display_api(request, monkeypatch):
    module, name = request.param
    constructions = []
    displays = []

    def create_walker(**kwargs):
        walker = SimpleNamespace(display_on_jupyter_use_widgets=lambda **options: displays.append(options))
        constructions.append((walker, kwargs))
        return walker

    monkeypatch.setattr(module, "PygWalker", create_walker)
    if module is webserver:
        monkeypatch.setattr(
            module,
            "_start_server",
            lambda walker, port, **options: displays.append({"walker": walker, "port": port, **options}),
        )
    return SimpleNamespace(
        module=module,
        name=name,
        call=getattr(module, name),
        constructions=constructions,
        displays=displays,
    )


def test_display_defaults_and_host_dispatch(display_api):
    dataset = object()

    assert display_api.call(dataset) is None

    walker, options = display_api.constructions[0]
    assert options == {
        "gid": None,
        "dataset": dataset,
        "field_specs": [],
        "spec": "",
        "source_invoke_code": "",
        "theme_key": "g2",
        "appearance": "media",
        "show_cloud_tool": False,
        "use_preview": False,
        "kernel_computation": None,
        "use_save_tool": False,
        "gw_mode": "filter_renderer" if display_api.name == "render" else "table",
        "is_export_dataframe": True,
        "kanaries_api_key": "",
        "default_tab": "vis",
        "cloud_computation": False,
    }
    if display_api.module is webserver:
        assert display_api.displays == [{"walker": walker, "port": None, "auto_open": False, "auto_shutdown": False}]
    else:
        assert display_api.displays == ([{}] if display_api.name == "render" else [{"iframe_height": "800px"}])


@pytest.mark.parametrize(
    ("computation", "kernel", "cloud"),
    [("auto", None, False), ("browser", False, False), ("kernel", True, False), ("cloud", False, True)],
)
def test_display_explicit_options_and_extra_props(display_api, tmp_path, computation, kernel, cloud):
    dataset = object()
    spec_path = tmp_path / "chart.json"
    extra_config = {"hideDataSourceConfig": True}
    host_options = {"port": 9001, "auto_open": True, "auto_shutdown": True} if display_api.module is webserver else {}

    assert (
        display_api.call(
            dataset,
            spec_path=spec_path,
            computation=computation,
            appearance="dark",
            theme_key="vega",
            kanaries_api_key="test-key",
            config=extra_config,
            **host_options,
        )
        is None
    )

    walker, options = display_api.constructions[0]
    assert options["dataset"] is dataset
    assert options["spec"] == str(spec_path)
    assert options["theme_key"] == "vega"
    assert options["appearance"] == "dark"
    assert options["kanaries_api_key"] == "test-key"
    assert options["kernel_computation"] is kernel
    assert options["cloud_computation"] is cloud
    assert options["config"] is extra_config
    assert not set(host_options).intersection(options)
    if display_api.module is webserver:
        assert display_api.displays == [{"walker": walker, **host_options}]


def test_display_legacy_warning_stays_at_public_entrypoint(display_api):
    with pytest.warns(DeprecationWarning, match="`kernel_computation` is deprecated") as warnings:
        display_api.call(object(), kernel_computation=False)

    assert len(warnings) == 1
    assert warnings[0].filename == display_api.module.__file__
    assert display_api.constructions[0][1]["kernel_computation"] is False


@pytest.mark.parametrize("conflicting_option", ["gid", "field_specs", "gw_mode", "cloud_computation"])
def test_display_extra_props_cannot_override_constructor_options(display_api, conflicting_option):
    with pytest.raises(TypeError, match=f"got multiple values for keyword argument '{conflicting_option}'"):
        display_api.call(object(), **{conflicting_option: "override"})

    assert display_api.constructions == []
    assert display_api.displays == []


def test_display_does_not_share_mutable_field_specs_between_calls(display_api):
    display_api.call(object())
    display_api.constructions[0][1]["field_specs"].append("changed")
    display_api.call(object())

    assert display_api.constructions[1][1]["field_specs"] == []


def test_display_invalid_computation_does_not_construct_or_display(display_api):
    with pytest.raises(ValueError, match="`computation` must be one of"):
        display_api.call(object(), computation="invalid")

    assert display_api.constructions == []
    assert display_api.displays == []
