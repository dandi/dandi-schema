"""
Validator drivers shared by the LinkML-behavior topic directories.

Each ``assert_*`` function checks one ``(target_class, instance)`` case
against one validator, so a topic's test modules carry only their case lists
and the ``@pytest.mark.parametrize`` decorators applying them. All three take
that case as their final positional arguments and an ``expect_pass`` keyword,
so a topic's three test modules stay parallel to one another.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
from types import ModuleType

from pydantic import ValidationError
import pytest


def _assert_returncode(
    result: subprocess.CompletedProcess[str],
    *,
    expect_pass: bool,
    target_class: str,
    instance: str,
) -> None:
    """Assert a CLI validator's exit status, reporting its output on failure."""
    expected_outcome = "pass" if expect_pass else "fail"
    assert (result.returncode == 0) is expect_pass, (
        f"expected validation to {expected_outcome} for {target_class} <- {instance}, "
        f"got rc={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def assert_linkml_validate(
    schema: Path, target_class: str, instance: str, *, expect_pass: bool
) -> None:
    """
    Assert how ``linkml-validate`` treats one case. ``instance`` is a filename
    resolved against the directory holding ``schema``.
    """
    result = subprocess.run(
        [
            "linkml-validate",
            "--schema",
            str(schema),
            "--target-class",
            target_class,
            str(schema.parent / instance),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    _assert_returncode(
        result, expect_pass=expect_pass, target_class=target_class, instance=instance
    )


def assert_check_jsonschema(
    json_schemas: dict[str, Path],
    json_instances: dict[str, Path],
    target_class: str,
    instance: str,
    *,
    expect_pass: bool,
) -> None:
    """
    Assert how ``check-jsonschema`` treats one case, given the generated
    per-class JSON schemas and the instances converted to JSON.

    ``check-jsonschema`` has JSON Schema ``format`` validation enabled by
    default (see https://check-jsonschema.readthedocs.io/en/stable/usage.html
    — disabled only via ``--disable-formats``).
    """
    result = subprocess.run(
        [
            "check-jsonschema",
            "--schemafile",
            str(json_schemas[target_class]),
            str(json_instances[instance]),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    _assert_returncode(
        result, expect_pass=expect_pass, target_class=target_class, instance=instance
    )


def assert_pydantic_validate(
    pydantic_module: ModuleType,
    instance_data: dict[str, dict],
    target_class: str,
    instance: str,
    *,
    expect_pass: bool,
) -> None:
    """
    Assert how the generated Pydantic models treat one case, given the loaded
    module and the instances parsed into dicts.
    """
    model = getattr(pydantic_module, target_class)
    if expect_pass:
        model.model_validate(instance_data[instance])
    else:
        with pytest.raises(ValidationError):
            model.model_validate(instance_data[instance])
