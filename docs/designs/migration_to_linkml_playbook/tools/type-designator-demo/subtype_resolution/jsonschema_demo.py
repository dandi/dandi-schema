"""
Demo (JSON Schema) — subtype resolution through a superclass-typed slot.

The counterpart to pydantic_demo.py. JSON Schema only validates -- it does not
return a typed object -- so the divergence is observed through the Project-only
`project_name` field on the shared `BareAsset` instance.

We validate the same instance against the `BareAsset` definition in each
generated JSON Schema (in `../schemas/`) and assert:

- schema_no_type_designator.json: INVALID. `wasGeneratedBy.items` is
  `$ref: Activity`, and Activity has `additionalProperties: false`, so the
  Project-only `project_name` is rejected.
- schema_type_designator.json: VALID. `wasGeneratedBy.items` is
  `anyOf: [Activity, Project]`, so the item matches the Project branch, which
  permits `project_name`.

Run from the repo root with the env that has jsonschema, e.g.:
    hatch run linkml-auto-converted:python \
        docs/designs/migration_to_linkml_playbook/tools/type-designator-demo/subtype_resolution/jsonschema_demo.py
"""

import json
from pathlib import Path

from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

HERE = Path(__file__).resolve().parent
SCHEMAS = HERE.parent / "schemas"
INSTANCE = json.loads((HERE / "bareasset_instance.json").read_text())


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

    # No-type-designator schema: the Project-only `project_name` is an
    # additional property on Activity, which forbids them -> instance rejected.
    assert not no_type_designator.is_valid(INSTANCE)

    # Type-designator schema: the item matches the Project branch of the
    # anyOf range, which permits `project_name` -> the instance validates.
    assert type_designator.is_valid(INSTANCE)

    print("All assertions passed.")


if __name__ == "__main__":
    main()
