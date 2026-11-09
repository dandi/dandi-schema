"""
Shared `(target_class, instance)` case lists for the validation tests in
this directory. Kept here so adding or adjusting a case updates every
test file that exercises the same schema/instances against a different
validator.
"""

from __future__ import annotations

PASSING_CASES: list[tuple[str, str]] = [
    # Baseline, before any respecification: `DeclaredRangeHolder` declares
    # the slot with `range: RangeBase`, and a `RangeBase` value is accepted.
    ("DeclaredRangeHolder", "range_base_instance.yaml"),
    # Under that same declared range, a value of any `RangeBase` subclass is
    # accepted as well, because `schemaKey` is a type designator, which makes
    # a class-valued range expand over the class's descendants. See the
    # `designates_type` finding in
    # `docs/designs/migration_to_linkml_playbook/findings.md`.
    ("DeclaredRangeHolder", "range_subclass_instance.yaml"),
    ("DeclaredRangeHolder", "range_sibling_subclass_instance.yaml"),
    ("DeclaredRangeHolder", "two_range_subclasses_instance.yaml"),
    # `NarrowedRangeHolder` narrows the inherited range to `RangeSubclass`
    # through `slot_usage`, and a `RangeSubclass` value is accepted.
    ("NarrowedRangeHolder", "range_subclass_instance.yaml"),
    # The slot stays multivalued across the narrowing.
    ("NarrowedRangeHolder", "two_range_subclasses_instance.yaml"),
    # `AnyOfRangeHolder` widens the inherited range to `Any` plus an
    # `any_of`, and a value of either class the `any_of` names is accepted.
    ("AnyOfRangeHolder", "range_base_instance.yaml"),
    ("AnyOfRangeHolder", "range_subclass_instance.yaml"),
    # A `RangeSiblingSubclass` value is accepted too, even though the
    # `any_of` does not name that class, because naming `RangeBase` already
    # covers every class below it. Listing a subclass alongside its base in
    # an `any_of` is therefore redundant, which is the
    # `BareAsset.wasGeneratedBy` situation in miniature.
    ("AnyOfRangeHolder", "range_sibling_subclass_instance.yaml"),
    # The slot stays multivalued across the widening.
    ("AnyOfRangeHolder", "two_range_subclasses_instance.yaml"),
]

FAILING_CASES: list[tuple[str, str]] = [
    # The narrowing genuinely constrains: under `range: RangeSubclass`,
    # neither a `RangeBase` value...
    ("NarrowedRangeHolder", "range_base_instance.yaml"),
    # ... nor a `RangeSiblingSubclass` value is accepted.
    ("NarrowedRangeHolder", "range_sibling_subclass_instance.yaml"),
    # An `OutsideRangeHierarchy` value is rejected by every holder. For
    # `AnyOfRangeHolder` this is the assertion that `range: Any` does not
    # degrade the slot into accepting anything at all.
    ("DeclaredRangeHolder", "outside_hierarchy_instance.yaml"),
    ("NarrowedRangeHolder", "outside_hierarchy_instance.yaml"),
    ("AnyOfRangeHolder", "outside_hierarchy_instance.yaml"),
]
