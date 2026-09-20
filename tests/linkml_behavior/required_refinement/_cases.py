"""
Shared `(target_class, instance)` case lists for the validation tests in
this directory. Kept here so adding or adjusting a case updates every
test file that exercises the same schema/instances against a different
validator.
"""

from __future__ import annotations

PASSING_CASES: list[tuple[str, str]] = [
    # Child requires `name`; instance supplies a string value
    # matching the inherited `range: string` -> valid.
    ("Employee", "valid_instance.yaml"),
    # Parent class leaves `name` optional -> a missing-name instance
    # is valid.
    ("Person", "missing_name_instance.yaml"),
    # Parent class leaves `name` optional; a string value satisfies
    # the slot's `range: string` -> valid.
    ("Person", "valid_instance.yaml"),
]

FAILING_CASES: list[tuple[str, str]] = [
    # The core assertion of issue #405: the child's `required: True`
    # override is honored.
    ("Employee", "missing_name_instance.yaml"),
    # The inherited `range: string` survives the refinement on the child.
    ("Employee", "bad_type_instance.yaml"),
    # `range: string` is also enforced on the parent class itself.
    ("Person", "bad_type_instance.yaml"),
]
