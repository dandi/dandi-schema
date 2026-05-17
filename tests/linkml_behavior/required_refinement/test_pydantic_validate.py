"""
Tests that the Pydantic models generated from the LinkML schema via
``gen-pydantic --black --template-dir <...>`` (matching the invocation
used in ``pyproject.toml``'s ``linkml-auto-converted:2pydantic`` script)
honor a ``slot_usage`` entry that refines an inherited slot from
``required: False`` to ``required: True`` while preserving the slot's
other inherited constraints (here, ``range``). This is the LinkML
behavior that the LinkML version of `dandischema` relies on.

See https://github.com/dandi/dandi-schema/issues/405.
"""

from __future__ import annotations

from types import ModuleType

from _cases import FAILING_CASES, PASSING_CASES
from pydantic import ValidationError
import pytest


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
