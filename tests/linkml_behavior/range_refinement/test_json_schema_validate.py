"""
Tests that the JSON schema generated from the LinkML schema via
``gen-json-schema --title-from title`` (matching the invocation used in
``pyproject.toml``'s ``linkml-auto-converted:2json`` script) honors a
``slot_usage`` entry that respecifies the range of an inherited multivalued
slot, both when the new range is a subclass of the inherited one and when it
is ``Any`` constrained by an ``any_of``. These are the LinkML behaviors that
the LinkML version of `dandischema` relies on for the ``wasGeneratedBy``
range overrides carried in ``dandischema/models_merge.yaml``.

Validation is performed via the ``check-jsonschema`` CLI, which has JSON
Schema ``format`` validation enabled by default (see
https://check-jsonschema.readthedocs.io/en/stable/usage.html — disabled
only via ``--disable-formats``).
"""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from ._cases import FAILING_CASES, PASSING_CASES


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


@pytest.mark.parametrize(("target_class", "instance"), PASSING_CASES)
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


@pytest.mark.parametrize(("target_class", "instance"), FAILING_CASES)
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
