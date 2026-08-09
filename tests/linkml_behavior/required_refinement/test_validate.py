"""
Tests that `linkml-validate` honors a `slot_usage` entry that refines an
inherited slot from `required: False` to `required: True` while preserving
the slot's other inherited constraints (here, `range`). This is the
LinkML behavior that the LinkML version of `dandischema` relies on.

See https://github.com/dandi/dandi-schema/issues/405.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ._cases import FAILING_CASES, PASSING_CASES
from .._validators import assert_linkml_validate

SCHEMA = Path(__file__).parent / "schema.yaml"


@pytest.mark.parametrize(("target_class", "instance"), PASSING_CASES)
def test_validation_passes(target_class: str, instance: str) -> None:
    assert_linkml_validate(SCHEMA, target_class, instance, expect_pass=True)


@pytest.mark.parametrize(("target_class", "instance"), FAILING_CASES)
def test_validation_fails(target_class: str, instance: str) -> None:
    assert_linkml_validate(SCHEMA, target_class, instance, expect_pass=False)
