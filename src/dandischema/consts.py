DANDI_SCHEMA_VERSION = "0.4.4"
ALLOWED_INPUT_SCHEMAS = ["0.3.0", "0.3.1", "0.4.0", "0.4.1", "0.4.2", "0.4.3"]

# ATM we allow only for a single target version which is current
# migrate has a guard now for this since it cannot migrate to anything but current
# version
ALLOWED_TARGET_SCHEMAS = [DANDI_SCHEMA_VERSION]

if DANDI_SCHEMA_VERSION not in ALLOWED_INPUT_SCHEMAS:
    ALLOWED_INPUT_SCHEMAS.append(DANDI_SCHEMA_VERSION)
