"""Find Pydantic models where schemaKey default != class name."""

import inspect
import sys

from pydantic import BaseModel

import dandischema.models as mod

# The set of the names of classes where the schemaKey default doesn't match the class
# name in the last recorded inspection of this script
LAST_SCHEMAKEY_MISMATCHES = {"BareAsset", "PublishedAsset", "PublishedDandiset"}

# The set of the names of classes where the schemaKey default doesn't match the class
# name
schemakey_mismatches: set[str] = set()

for name, cls in inspect.getmembers(mod, inspect.isclass):
    # Only consider Pydantic models
    if not issubclass(cls, BaseModel) or cls is BaseModel:
        continue
    # Skip re-exported classes defined in other modules
    if cls.__module__ != mod.__name__:
        continue

    fields = cls.model_fields
    # Only look at models that have a schemaKey field
    if "schemaKey" not in fields:
        continue

    field = fields["schemaKey"]
    schema_key_default = field.default
    # Flag models where the schemaKey default doesn't match the class name,
    # including cases where the default is None (i.e. not explicitly set)
    if schema_key_default != name:
        print(f"{name}: schemaKey default = {schema_key_default!r}")
        schemakey_mismatches.add(name)

print("---------------")
if schemakey_mismatches == LAST_SCHEMAKEY_MISMATCHES:
    print("No changes since last inspection.")
else:
    print("WARNING: Changes since last inspection!")
    print(f"New mismatches: {schemakey_mismatches - LAST_SCHEMAKEY_MISMATCHES}")
    print(f"Resolved mismatches: {LAST_SCHEMAKEY_MISMATCHES - schemakey_mismatches}")
    sys.exit(1)
