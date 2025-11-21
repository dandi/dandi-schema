from packaging.version import Version as _Version

DANDI_SCHEMA_VERSION = "0.7.0"
ALLOWED_INPUT_SCHEMAS = [
    "0.4.4",
    "0.5.1",
    "0.5.2",
    "0.6.0",
    "0.6.1",
    "0.6.2",
    "0.6.3",
    "0.6.4",
    "0.6.5",
    "0.6.6",
    "0.6.7",
    "0.6.8",
    "0.6.9",
    "0.6.10",
    DANDI_SCHEMA_VERSION,
]

# We establish migrations (back) to only a few recent versions.
# When adding changes, please consider whether a migration path should be added.
ALLOWED_TARGET_SCHEMAS = ["0.6.10", DANDI_SCHEMA_VERSION]

# This allows multiple schemas for validation, whereas target schemas focus on
# migration.
ALLOWED_VALIDATION_SCHEMAS = sorted(
    set(ALLOWED_INPUT_SCHEMAS).union(ALLOWED_TARGET_SCHEMAS), key=_Version
)
