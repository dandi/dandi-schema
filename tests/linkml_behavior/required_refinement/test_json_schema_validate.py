"""
Tests that the JSON schema generated from the LinkML schema via
``gen-json-schema --title-from title`` (matching the invocation used in
``pyproject.toml``'s ``linkml-auto-converted:2json`` script) honors a
``slot_usage`` entry that refines an inherited slot from ``required: False``
to ``required: True`` while preserving the slot's other inherited
constraints (here, ``range``). This is the LinkML behavior that the LinkML
version of `dandischema` relies on.

Validation is performed via the ``check-jsonschema`` CLI, which has JSON
Schema ``format`` validation enabled by default (see
https://check-jsonschema.readthedocs.io/en/stable/usage.html — disabled
only via ``--disable-formats``).

See https://github.com/dandi/dandi-schema/issues/405.
"""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest


def _validate(schema: Path, instance: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "check-jsonschema",
            "--schemafile",
            str(schema),
            str(instance),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("target_class", "instance"),
    [
        # Child requires `name`; instance supplies a string value
        # matching the inherited `range: string` -> valid.
        ("Employee", "valid_instance.yaml"),
        # Parent class leaves `name` optional -> a missing-name instance
        # is valid.
        ("Person", "missing_name_instance.yaml"),
        # Parent class leaves `name` optional; a string value satisfies
        # the slot's `range: string` -> valid.
        ("Person", "valid_instance.yaml"),
    ],
)
def test_validation_passes(
    target_class: str,
    instance: str,
    json_schemas: dict[str, Path],
    json_instances: dict[str, Path],
) -> None:
    result = _validate(json_schemas[target_class], json_instances[instance])
    assert result.returncode == 0, (
        f"expected validation to pass for {target_class} <- {instance}, "
        f"got rc={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.parametrize(
    ("target_class", "instance"),
    [
        # The core assertion of issue #405: the child's `required: True`
        # override is honored.
        ("Employee", "missing_name_instance.yaml"),
        # The inherited `range: string` survives the refinement on the child.
        ("Employee", "bad_type_instance.yaml"),
        # `range: string` is also enforced on the parent class itself.
        ("Person", "bad_type_instance.yaml"),
    ],
)
def test_validation_fails(
    target_class: str,
    instance: str,
    json_schemas: dict[str, Path],
    json_instances: dict[str, Path],
) -> None:
    result = _validate(json_schemas[target_class], json_instances[instance])
    assert result.returncode != 0, (
        f"expected validation to fail for {target_class} <- {instance}, "
        f"got rc={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
