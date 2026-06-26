import inspect
from typing import Any, Callable, Collection, Dict, List, Mapping, Optional


def is_public_walker(value: Any) -> bool:
    from pygwalker.api.walker import Walker

    return isinstance(value, Walker)


def get_callable_defaults(callable_obj: Callable[..., Any], names: Collection[str]) -> Dict[str, Any]:
    """Return declared defaults for a public adapter entrypoint."""
    signature = inspect.signature(callable_obj)
    defaults: Dict[str, Any] = {}
    for name in names:
        parameter = signature.parameters[name]
        if parameter.default is inspect.Parameter.empty:
            raise ValueError(f"`{name}` has no default in {callable_obj.__name__}")
        defaults[name] = parameter.default
    return defaults


def collect_walker_construction_conflicts(
    values: Mapping[str, Any],
    defaults: Mapping[str, Any],
    *,
    empty_defaults: Collection[str] = ("spec",),
    truthy_conflicts: Collection[str] = ("kanaries_api_key",),
    conflict_predicates: Optional[Mapping[str, Callable[[Any], bool]]] = None,
    extra_kwargs: Optional[Dict[str, Any]] = None,
    present_extra_conflicts: Collection[str] = (),
) -> List[str]:
    conflicts: List[str] = []
    conflict_predicates = conflict_predicates or {}

    for name, value in values.items():
        if name in conflict_predicates:
            has_conflict = conflict_predicates[name](value)
        elif name in empty_defaults:
            has_conflict = value not in ("", None)
        elif name in truthy_conflicts:
            has_conflict = bool(value)
        else:
            has_conflict = value != defaults[name]

        if has_conflict:
            conflicts.append(name)

    if extra_kwargs:
        conflicts.extend(name for name in present_extra_conflicts if name in extra_kwargs)
        conflicts.extend(sorted(name for name in extra_kwargs if name not in present_extra_conflicts))

    return conflicts


def reject_walker_construction_params(caller: str, conflicts: List[str]) -> None:
    if not conflicts:
        return

    params = ", ".join(conflicts)
    raise ValueError(
        f"{caller} received a Walker object and cannot apply construction parameters: {params}. "
        "Pass those options when creating pygwalker.Walker instead."
    )
