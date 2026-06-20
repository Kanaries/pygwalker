import warnings
from typing import Optional, Tuple

from pygwalker._typing import IComputation
from pygwalker.data_parsers.database_parser import Connector
from pygwalker.utils import fallback_value


def _is_connector_dataset(dataset) -> bool:
    return isinstance(dataset, (Connector, str))


def _warn_legacy_computation_param(name: str, replacement: str) -> None:
    warnings.warn(
        f"`{name}` is deprecated and will be removed in a future release; use `{replacement}` instead.",
        DeprecationWarning,
        stacklevel=3,
    )


def resolve_computation_mode(
    dataset: object,
    *,
    computation: Optional[IComputation] = None,
    kernel_computation: Optional[bool] = None,
    cloud_computation: bool = False,
    use_kernel_calc: Optional[bool] = None,
    default_kernel_computation: Optional[bool] = None,
    force_kernel_for_connectors: bool = True,
) -> Tuple[Optional[bool], bool]:
    """Resolve public computation options to internal kernel/cloud flags."""
    if computation is not None and computation not in ("auto", "browser", "kernel", "cloud"):
        raise ValueError("`computation` must be one of 'auto', 'browser', 'kernel', or 'cloud'.")

    explicit_auto = computation == "auto"
    if computation is not None and not explicit_auto:
        enabled_legacy_params = []
        if kernel_computation is True:
            enabled_legacy_params.append("kernel_computation")
        if cloud_computation is True:
            enabled_legacy_params.append("cloud_computation")
        if use_kernel_calc is True:
            enabled_legacy_params.append("use_kernel_calc")
        if enabled_legacy_params:
            legacy_names = ", ".join(enabled_legacy_params)
            raise ValueError(
                f"`computation` replaces legacy computation flags; remove {legacy_names} "
                "or express the mode with `computation` only."
            )

        if computation == "browser":
            return False, False
        if computation == "kernel":
            return True, False
        if computation == "cloud":
            return False, True

    if kernel_computation is not None:
        _warn_legacy_computation_param("kernel_computation", "computation='kernel' or computation='browser'")
    if cloud_computation:
        _warn_legacy_computation_param("cloud_computation", "computation='cloud'")
    if use_kernel_calc is not None:
        _warn_legacy_computation_param("use_kernel_calc", "computation='kernel' or computation='browser'")

    if cloud_computation:
        return False, True

    use_kernel = fallback_value(kernel_computation, use_kernel_calc, default_kernel_computation)
    if force_kernel_for_connectors and _is_connector_dataset(dataset):
        return True, False
    if use_kernel is None:
        return None, False
    return bool(use_kernel), False
