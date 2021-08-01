schema_info = {
    "version": "1.0.0",
    "schema_version": "0.5.1",
    "process": {"0.5.1": None, "0.4.4": "migrate"},
}

DANDI_SCHEMA_VERSION = schema_info["schema_version"]
ALLOWED_SCHEMAS = list(schema_info["process"])

# ATM we allow only for a single target version which is current
# migrate has a guard now for this since it cannot migrate to anything but current
# version
ALLOWED_TARGET_SCHEMAS = [DANDI_SCHEMA_VERSION]

if DANDI_SCHEMA_VERSION not in ALLOWED_SCHEMAS:
    ALLOWED_SCHEMAS.append(DANDI_SCHEMA_VERSION)
