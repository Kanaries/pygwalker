import pytest

from pygwalker.utils.computation import resolve_computation_mode


@pytest.mark.parametrize(
    ("computation", "expected"),
    [
        ("auto", (None, False)),
        ("browser", (False, False)),
        ("kernel", (True, False)),
        ("cloud", (False, True)),
    ],
)
def test_resolve_computation_mode_from_new_api(computation, expected):
    assert resolve_computation_mode(object(), computation=computation) == expected


def test_resolve_computation_mode_preserves_unspecified_auto_detection():
    assert resolve_computation_mode(object()) == (None, False)


def test_resolve_computation_mode_rejects_invalid_mode():
    with pytest.raises(ValueError, match="`computation` must be one of"):
        resolve_computation_mode(object(), computation="remote")


def test_resolve_computation_mode_rejects_enabled_legacy_flags_with_new_api():
    with pytest.raises(ValueError, match="replaces legacy computation flags"):
        resolve_computation_mode(object(), computation="browser", kernel_computation=True)


@pytest.mark.parametrize(
    ("legacy_kwargs", "expected_message_fragment"),
    [
        ({"kernel_computation": True}, "kernel_computation"),
        ({"cloud_computation": True}, "cloud_computation"),
        ({"use_kernel_calc": True}, "use_kernel_calc"),
    ],
)
def test_resolve_computation_mode_rejects_each_enabled_legacy_flag_with_new_api(
    legacy_kwargs,
    expected_message_fragment,
):
    with pytest.raises(ValueError, match=expected_message_fragment):
        resolve_computation_mode(object(), computation="browser", **legacy_kwargs)


def test_resolve_computation_mode_preserves_default_kernel_semantics():
    assert resolve_computation_mode(object(), default_kernel_computation=True) == (True, False)


def test_resolve_computation_mode_warns_for_legacy_kernel_param():
    with pytest.warns(DeprecationWarning, match="kernel_computation.*0\\.7\\.0"):
        assert resolve_computation_mode(object(), kernel_computation=True) == (True, False)


@pytest.mark.parametrize(
    ("legacy_kwargs", "expected_result", "expected_warning"),
    [
        ({"kernel_computation": True}, (True, False), "kernel_computation.*0\\.7\\.0"),
        ({"cloud_computation": True}, (False, True), "cloud_computation.*0\\.7\\.0"),
        ({"use_kernel_calc": True}, (True, False), "use_kernel_calc.*0\\.7\\.0"),
    ],
)
def test_resolve_computation_mode_warns_and_preserves_each_legacy_flag(
    legacy_kwargs,
    expected_result,
    expected_warning,
):
    with pytest.warns(DeprecationWarning, match=expected_warning):
        assert resolve_computation_mode(object(), **legacy_kwargs) == expected_result
