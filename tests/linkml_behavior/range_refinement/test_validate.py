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
