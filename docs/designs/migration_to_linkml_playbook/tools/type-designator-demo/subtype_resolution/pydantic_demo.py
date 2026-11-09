"""
Demo (Pydantic) — subtype resolution through a superclass-typed slot.

How the `wasGeneratedBy` slot range differs between the two generated Pydantic
modules (in `../schemas/`) when fed the shared `BareAsset` instance whose
`wasGeneratedBy` list holds a single *Project* carrying the Project-only
`project_name` field.

- models_no_type_designator.py -> slot range is `list[Activity]`
- models_type_designator.py    -> slot range is `list[Union[Activity, Project]]`
  (the `schemaKey` type designator expands the range over Activity's descendants)

Asserts:
- no-type-designator module: validation FAILS -- the item is checked against
  `Activity`, which forbids the extra `project_name` field.
- type-designator module: the item resolves to the concrete `Project` type and
  keeps `project_name`.

Run from the repo root with an env that has pydantic, e.g.:
    hatch run linkml-auto-converted:python \
        docs/designs/migration_to_linkml_playbook/tools/type-designator-demo/subtype_resolution/pydantic_demo.py
"""

import json
from pathlib import Path
import sys

SCHEMAS = Path(__file__).resolve().parent.parent / "schemas"
sys.path.insert(0, str(SCHEMAS))

import models_no_type_designator  # noqa: E402
import models_type_designator  # noqa: E402
from pydantic import ValidationError  # noqa: E402

INSTANCE = json.loads((Path(__file__).parent / "bareasset_instance.json").read_text())


def main() -> None:
    # No-type-designator module: the slot range is `list[Activity]`, and
    # Activity forbids extra fields, so the Project-only `project_name` makes
    # validation fail.
    try:
        models_no_type_designator.BareAsset.model_validate(INSTANCE)
    except ValidationError:
        pass
    else:
        raise AssertionError(
            "expected no-type-designator module to reject the Project item"
        )

    # Type-designator module: the slot range expands to
    # `list[Union[Activity, Project]]`, so the item resolves to the concrete
    # Project type and `project_name` is preserved.
    item = models_type_designator.BareAsset.model_validate(INSTANCE).wasGeneratedBy[0]
    assert type(item) is models_type_designator.Project
    assert item.project_name == "My Project"

    print("All assertions passed.")


if __name__ == "__main__":
    main()
