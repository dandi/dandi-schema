"""
Tests that the Pydantic models generated from the LinkML schema via
``gen-pydantic --black --template-dir <...>`` (matching the invocation used
in ``pyproject.toml``'s ``linkml-auto-converted:2pydantic`` script) honor a
``slot_usage`` entry that respecifies the range of an inherited multivalued
slot, both when the new range is a subclass of the inherited one and when it
is ``Any`` constrained by an ``any_of``. These are the LinkML behaviors that
the LinkML version of `dandischema` relies on for the ``wasGeneratedBy``
range overrides carried in ``dandischema/models_merge.yaml``.
"""

from __future__ import annotations

from types import ModuleType

from pydantic import ValidationError
import pytest

from ._cases import FAILING_CASES, PASSING_CASES


@pytest.mark.parametrize(("target_class", "instance"), PASSING_CASES)
def test_validation_passes(
    target_class: str,
    instance: str,
    pydantic_module: ModuleType,
    instance_data: dict[str, dict],
) -> None:
    cls = getattr(pydantic_module, target_class)
    cls.model_validate(instance_data[instance])


@pytest.mark.parametrize(("target_class", "instance"), FAILING_CASES)
def test_validation_fails(
    target_class: str,
    instance: str,
    pydantic_module: ModuleType,
    instance_data: dict[str, dict],
) -> None:
    cls = getattr(pydantic_module, target_class)
    with pytest.raises(ValidationError):
        cls.model_validate(instance_data[instance])
