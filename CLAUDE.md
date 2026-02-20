# CLAUDE.md

This file provides guidance to Claude Code when working with code in this
repository.

## Project Overview

dandischema defines the Pydantic v2 metadata models for the DANDI
neurophysiology data archive.  It is used by both the dandi-cli client and the
dandi-archive server.  Key concerns: model definitions, JSON Schema generation,
metadata validation, schema migration between versions, and asset metadata
aggregation.

## Build/Test Commands

```bash
tox -e py3                    # Run full test suite (preferred)
pytest dandischema/           # Run tests directly in active venv
pytest dandischema/tests/test_metadata.py -v -k "test_name"  # Single test
tox -e lint                   # codespell + flake8
tox -e typing                 # mypy (strict, with pydantic plugin)
```

- `filterwarnings = error` is active — new warnings will fail tests.
- Coverage is collected by default (`--cov=dandischema`).

## Code Style

- **Formatter**: Black (no explicit line-length override → default 88)
- **Import sorting**: isort with `profile = "black"`, `force_sort_within_sections`,
  `reverse_relative`
- **Linting**: flake8 (max-line-length=100, ignores E203/W503)
- **Type checking**: mypy strict — `no_implicit_optional`, `warn_return_any`,
  `warn_unreachable`, pydantic plugin enabled
- **Pre-commit hooks**: trailing-whitespace, end-of-file-fixer, check-yaml,
  check-added-large-files, black, isort, codespell, flake8
- Imports at top of file; avoid function-level imports unless there is a
  concrete reason (circular deps, heavy transitive imports)

## Architecture

### Key Modules

| File | Role |
|------|------|
| `models.py` | All Pydantic models (~2000 lines). Class hierarchy rooted at `DandiBaseModel`. |
| `metadata.py` | `validate()`, `migrate()`, `aggregate_assets_summary()`. |
| `consts.py` | `DANDI_SCHEMA_VERSION`, `ALLOWED_INPUT_SCHEMAS`, `ALLOWED_TARGET_SCHEMAS`. |
| `conf.py` | Instance configuration via env vars (`DANDI_INSTANCE_NAME`, etc.). |
| `types.py` | Custom Pydantic types (`ByteSizeJsonSchema`). |
| `utils.py` | JSON schema helpers, `version2tuple()`, `name2title()`. |
| `exceptions.py` | `ValidationError`, `JsonschemaValidationError`, `PydanticValidationError`. |
| `digests/` | `DandiETag` multipart-upload checksum calculation. |
| `datacite/` | DataCite DOI metadata conversion. |

### Model Hierarchy (simplified)

```
DandiBaseModel
├── PropertyValue          # recursive (self-referencing)
├── BaseType
│   ├── StandardsType      # name, identifier, version, extensions (recursive)
│   ├── ApproachType, AssayType, SampleType, Anatomy, ...
│   └── MeasurementTechniqueType
├── Person, Organization   # Contributor subclasses
├── BioSample              # recursive (wasDerivedFrom)
├── AssetsSummary          # aggregated stats
└── CommonModel
    ├── Dandiset → PublishedDandiset
    └── BareAsset → Asset → PublishedAsset
```

Several models are **self-referencing** (PropertyValue, BioSample,
StandardsType).  These require `model_rebuild()` after the class definition.

### Data Flow: Asset Metadata Aggregation

1. dandi-cli calls `asset.get_metadata()` → populates `BareAsset` including
   per-asset `dataStandard` list
2. Asset metadata is serialized via `model_dump(mode="json", exclude_none=True)`
3. Server calls `aggregate_assets_summary(assets)` →
   `_add_asset_to_stats()` per asset → `AssetsSummary`
4. `_add_asset_to_stats()` collects: numberOfBytes, numberOfFiles, approach,
   measurementTechnique, variableMeasured, species, subjects, dataStandard
5. `dataStandard` has deprecated path/encoding heuristic fallbacks for old
   clients (remove after 2026-12-01)

### Pre-instantiated Standard Constants

```python
nwb_standard   # RRID:SCR_015242
bids_standard  # RRID:SCR_016124
ome_ngff_standard  # DOI:10.25504/FAIRsharing.9af712
hed_standard   # RRID:SCR_014074
```

These are dicts (`model_dump(mode="json", exclude_none=True)`) used by both
dandischema (heuristic fallbacks) and dandi-cli (per-asset population).

### Vendorization

The schema supports deployment for different DANDI instances.  Environment
variables (`DANDI_INSTANCE_NAME`, `DANDI_INSTANCE_IDENTIFIER`,
`DANDI_DOI_PREFIX`, etc.) must be set **before** importing
`dandischema.models`.  This dynamically adjusts identifier patterns, DOI
prefixes, license enums, and URL patterns.  CI tests multiple vendored
configurations.

## Schema Change Checklist

When adding or removing fields from any model (BareAsset, Dandiset,
AssetsSummary, etc.):

1. **Update `_FIELDS_INTRODUCED` in `metadata.py:migrate()`** if adding a new
   **top-level field to Dandiset metadata** — `migrate()` only processes
   Dandiset-level dicts (not Asset metadata).  Fields on BareAsset or nested
   inside existing structures (e.g. new fields on StandardsType) do not need
   entries here.

2. **Update `consts.py`** if bumping `DANDI_SCHEMA_VERSION` or adding to
   `ALLOWED_INPUT_SCHEMAS`.

3. **Add tests** covering migration/aggregation with the new field.

4. **Coordinate with dandi-cli** — new fields that dandi-cli populates need
   backward-compat guards there (check `"field" in Model.model_fields`) until
   the minimum dandischema dependency is bumped.

## Testing Notes

- Tests use `filterwarnings = error` — any new deprecation warning will fail.
- The `clear_dandischema_modules_and_set_env_vars` fixture (conftest.py)
  supports testing vendored configurations by clearing cached modules and
  setting env vars.
- Network-dependent tests are skipped when `DANDI_TESTS_NONETWORK` is set.
- DataCite tests require `DATACITE_DEV_LOGIN` / `DATACITE_DEV_PASSWORD`.
- `test_models.py:test_duplicate_classes` checks for duplicate field qnames
  across models; allowed duplicates are listed explicitly.
