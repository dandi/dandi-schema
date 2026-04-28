from __future__ import annotations

from importlib.metadata import PackageNotFoundError, requires, version

from packaging.requirements import Requirement
from pytest import Config

from dandischema.models import DandiBaseModel


def pytest_configure(config: Config) -> None:
    markers = [
        "ai_generated",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def pytest_report_header(config: Config) -> list[str]:
    """Add version information for key dependencies to the pytest header."""
    try:
        deps = {Requirement(dep).name for dep in (requires("dandischema") or [])}
    except PackageNotFoundError:
        deps = {"jsonschema", "pydantic", "requests"}

    versions = []
    for pkg in sorted(deps):
        try:
            version_str = f"-{version(pkg)}"
        except PackageNotFoundError:
            version_str = " NOT INSTALLED"
        versions.append(f"{pkg}{version_str}")

    return [f"dependencies: {', '.join(versions)}"] if versions else []


def pytest_assertrepr_compare(op: str, left: object, right: object) -> list[str] | None:
    """Custom comparison representation for DandiBaseModel."""
    if (
        isinstance(left, DandiBaseModel)
        and isinstance(right, DandiBaseModel)
        and op == "=="
    ):
        ldict, rdict = dict(left), dict(right)
        if ldict == rdict:
            return [
                "dict representations of models are equal, but values aren't!",
                f"Left: {left!r}",
                f"Right: {right!r}",
            ]
        else:
            # Rely on pytest "recursing" into interpreting the dict diff.
            # TODO: could be further improved by accounting for ANY values etc.
            assert ldict == rdict  # for easier comprehension of diffs
    return None
