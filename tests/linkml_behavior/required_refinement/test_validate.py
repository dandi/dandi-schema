"""
Tests that `linkml-validate` honors a `slot_usage` entry that refines an
inherited slot from `required: False` to `required: True` while preserving
the slot's other inherited constraints (here, `range`). This is the
LinkML behavior that the LinkML version of `dandischema` relies on.

See https://github.com/dandi/dandi-schema/issues/405.
"""

from __future__ import annotations

from pathlib import Path
import subprocess

from _cases import FAILING_CASES, PASSING_CASES
import pytest

HERE = Path(__file__).parent
SCHEMA = HERE / "schema.yaml"


def _validate(target_class: str, instance: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "linkml-validate",
            "--schema",
            str(SCHEMA),
            "--target-class",
            target_class,
            str(HERE / instance),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(("target_class", "instance"), PASSING_CASES)
def test_validation_passes(target_class: str, instance: str) -> None:
    result = _validate(target_class, instance)
    assert result.returncode == 0, (
        f"expected validation to pass for {target_class} <- {instance}, "
        f"got rc={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.parametrize(("target_class", "instance"), FAILING_CASES)
def test_validation_fails(target_class: str, instance: str) -> None:
    result = _validate(target_class, instance)
    assert result.returncode != 0, (
        f"expected validation to fail for {target_class} <- {instance}, "
        f"got rc={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
