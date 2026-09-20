"""
Demo (JSON Schema) — how `schemaKey` itself is validated, with and without the
type designator. The counterpart to pydantic_demo.py.

The four cases in `schemakey_cases.json` are validated against the `BareAsset`
definition in each generated JSON Schema (in `../schemas/`):

- schema_type_designator.json — `schemaKey: {enum: ["BareAsset"], type: [string, null]}`:
    valid       (in enum)                       -> valid
    absent      (schemaKey not required)        -> valid
    null        (enum excludes null, despite    -> invalid
                 `type` listing it)
    wrong_class (not in enum)                   -> invalid
- schema_no_type_designator.json — `schemaKey: {type: [string, null]}`:
    every case is valid (any string, null, or absent).

Note the `null` case: the type-designator `schemaKey` has both an `enum` and a
nullable `type`, but `null` is still rejected because `enum` does not list it --
JSON Schema requires every keyword to pass. This matches Pydantic's `Literal`
(pydantic_demo.py); there is no JSON-Schema-vs-Pydantic asymmetry here.

Run from the repo root with the env that has jsonschema, e.g.:
    hatch run linkml-auto-converted:python \
        docs/designs/migration_to_linkml_playbook/tools/type-designator-demo/schemakey_validation/jsonschema_demo.py
"""

import json
from pathlib import Path

from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

HERE = Path(__file__).resolve().parent
SCHEMAS = HERE.parent / "schemas"
CASES = json.loads((HERE / "schemakey_cases.json").read_text())

# Expected validity per case for the type-designator schema.
TYPE_DESIGNATOR_VALID = {
    "valid": True,
    "absent": True,
    "null": False,
    "wrong_class": False,
}


def bareasset_validator(schema_file: str) -> Validator:
    """Build a validator rooted at the schema's `BareAsset` definition."""
    full = json.loads((SCHEMAS / schema_file).read_text())
    schema = {
        "$schema": full["$schema"],
        "$ref": "#/$defs/BareAsset",
        "$defs": full["$defs"],
    }
    return validator_for(schema)(schema)


def main() -> None:
    no_type_designator = bareasset_validator("schema_no_type_designator.json")
    type_designator = bareasset_validator("schema_type_designator.json")

    for name, instance in CASES.items():
        # No-type-designator: schemaKey is an unconstrained nullable string, so
        # every case is valid.
        assert no_type_designator.is_valid(
            instance
        ), f"no-type-designator should accept {name}"
        # Type-designator: schemaKey is pinned to the class name via `enum`.
        assert (
            type_designator.is_valid(instance) is TYPE_DESIGNATOR_VALID[name]
        ), f"type-designator validity mismatch for {name}"

    print("All assertions passed.")


if __name__ == "__main__":
    main()
