from packaging.version import Version as _Version

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
    set(ALLOWED_INPUT_SCHEMAS).union(ALLOWED_TARGET_SCHEMAS), key=_Version
)

# Static patterns
NAME_PATTERN = r"^([\w\s\-\.']+),\s+([\w\s\-\.']+)$"
UUID_PATTERN = (
    "[a-f0-9]{8}[-]*[a-f0-9]{4}[-]*[a-f0-9]{4}[-]*[a-f0-9]{4}[-]*[a-f0-9]{12}$"
)
ASSET_UUID_PATTERN = r"^dandiasset:" + UUID_PATTERN
VERSION_PATTERN = r"\d{6}/\d+\.\d+\.\d+"
DANDI_NSKEY = "dandi"  # Namespace for DANDI ontology
MD5_PATTERN = r"[0-9a-f]{32}"
SHA256_PATTERN = r"[0-9a-f]{64}"
