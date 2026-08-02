"""
Tests that `linkml-validate` honors a `slot_usage` entry that respecifies
the range of an inherited multivalued slot, both when the new range is a
subclass of the inherited one and when it is `Any` constrained by an
`any_of`. These are the LinkML behaviors that the LinkML version of
`dandischema` relies on for the `wasGeneratedBy` range overrides carried in
`dandischema/models_merge.yaml`.
"""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from ._cases import FAILING_CASES, PASSING_CASES

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
