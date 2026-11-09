"""
Demo (Pydantic) — how `schemaKey` itself is validated, with and without the type
designator.

This verifies the constraint `designates_type: true` places on `schemaKey`, and
that it matches the JSON Schema side (see jsonschema_demo.py). The four cases in
`schemakey_cases.json` are validated against `BareAsset` from each generated
module (in `../schemas/`):

- type-designator module — `schemaKey: Literal["BareAsset"]` with a default:
    valid       (schemaKey == class name) -> accepted
    absent      (default fills it in)     -> accepted
    null        (Literal excludes None)   -> rejected
    wrong_class (Literal excludes it)     -> rejected
- no-type-designator module — `schemaKey: Optional[str]` with a default:
    every case is accepted (any string, None, or absent).

The point: with `designates_type: true`, Pydantic enforces the class name on
`schemaKey`; without it, `schemaKey` is an unconstrained optional string. Both
outcomes match the JSON Schema side exactly (jsonschema_demo.py).

Run from the repo root with an env that has pydantic, e.g.:
    hatch run linkml-auto-converted:python \
        docs/designs/migration_to_linkml_playbook/tools/type-designator-demo/schemakey_validation/pydantic_demo.py
"""

import json
from pathlib import Path
import sys

SCHEMAS = Path(__file__).resolve().parent.parent / "schemas"
sys.path.insert(0, str(SCHEMAS))

import models_no_type_designator  # noqa: E402
import models_type_designator  # noqa: E402
from pydantic import ValidationError  # noqa: E402

CASES = json.loads((Path(__file__).parent / "schemakey_cases.json").read_text())

# Expected acceptance per case for the type-designator module.
TYPE_DESIGNATOR_ACCEPTS = {
    "valid": True,
    "absent": True,
    "null": False,
    "wrong_class": False,
}


def accepts(model_cls: type, instance: dict) -> bool:
    try:
        model_cls.model_validate(instance)
    except ValidationError:
        return False
    return True


def main() -> None:
    for name, instance in CASES.items():
        # No-type-designator: schemaKey is an unconstrained optional string, so
        # every case is accepted.
        assert accepts(
            models_no_type_designator.BareAsset, instance
        ), f"no-type-designator should accept {name}"
        # Type-designator: schemaKey is pinned to the class name.
        assert (
            accepts(models_type_designator.BareAsset, instance)
            is TYPE_DESIGNATOR_ACCEPTS[name]
        ), f"type-designator acceptance mismatch for {name}"

    print("All assertions passed.")


if __name__ == "__main__":
    main()
