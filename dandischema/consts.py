DANDI_SCHEMA_VERSION = "0.6.10"
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
    DANDI_SCHEMA_VERSION,
]

# ATM we allow only for a single target version which is current
# migrate has a guard now for this since it cannot migrate to anything but current
# version
ALLOWED_TARGET_SCHEMAS = [DANDI_SCHEMA_VERSION]

# This allows multiple schemas for validation, whereas target schemas focus on
# migration.
ALLOWED_VALIDATION_SCHEMAS = sorted(
    set(ALLOWED_INPUT_SCHEMAS).union(ALLOWED_TARGET_SCHEMAS)
)
