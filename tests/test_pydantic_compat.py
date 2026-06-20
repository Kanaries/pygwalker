from pathlib import Path


PYDANTIC_V1_API_PATTERNS = (".dict(", ".parse_obj(")
PYDANTIC_COMPAT_MODULE = Path("pygwalker/utils/pydantic_compat.py")


def test_pydantic_v1_api_calls_stay_in_compat_module():
    repo_root = Path(__file__).resolve().parents[1]
    offenders = []

    for path in sorted((repo_root / "pygwalker").rglob("*.py")):
        relative_path = path.relative_to(repo_root)
        if relative_path == PYDANTIC_COMPAT_MODULE:
            continue
        source = path.read_text(encoding="utf-8")
        if any(pattern in source for pattern in PYDANTIC_V1_API_PATTERNS):
            offenders.append(str(relative_path))

    assert offenders == []
