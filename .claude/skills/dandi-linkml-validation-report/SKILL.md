---
name: dandi-linkml-validation-report
description: Generate a Markdown report assessing how `dandischema/models.yaml` (the LinkML schema) validates against real DANDI Archive Dandiset metadata after migrating each instance to the latest schema version. Use when the user wants to assess schema fitness across the archive, investigate a class of validation failure across many dandisets, or compare before/after for a schema change. Covers fetching raw metadata for every dandiset (draft + every published version), migrating each instance via `dandischema.metadata.migrate`, running closed-world JSON-schema validation on successfully-migrated instances via the LinkML Python API, and aggregating per-version results into a top-level README.md bucketed by target class (Dandiset / PublishedDandiset) × schemaVersion. Versions whose metadata can't be migrated are flagged in the report; validation is skipped for them.
compatibility: Requires the `linkml-auto-converted` hatch env defined in this repo's pyproject.toml (provides linkml, linkml-runtime, dandi, typer) and network access to a DANDI Archive instance.
allowed-tools: Bash(git:*) Bash(hatch:*) Read
---

# DANDI LinkML validation report

Three-stage pipeline that fetches Dandiset metadata, validates it against
`dandischema/models.yaml`, and aggregates the results into a Markdown
report. Each stage is a Typer-based script under `scripts/`; each is
idempotent and resumable.

## When to use

- After updating the LinkML schema (or its Pydantic source in
  `dandischema.models`) — see what breaks across the archive.
- To investigate the spread of a specific validation failure across
  dandisets.
- To produce a before/after diff of schema changes.

## Prerequisites

- The `linkml-auto-converted` hatch env exists (defined in
  `pyproject.toml`).
- `dandischema/models.yaml` is present and reflects the schema you want
  to validate against. Typically, you stay on the `linkml-conversion`
  branch and pull the YAML from the auto-generated branch:

  ```sh
  git restore --source linkml-auto-converted -- dandischema/models.yaml
  ```

- Network access to the target DANDI instance (default: dani).

## Workflow

The pipeline writes everything under one flat directory:

```sh
ROOT=linkml-validation-reports
```

Raw metadata is schema-independent and only fetched once; subsequent
runs reuse it. Schema-dependent files (`metadata_migrated.json`,
`validation.{json,txt}`, `SUMMARY.md`, top-level `README.md`) are
rewritten in place when the schema content changes.

### 1. Fetch metadata

```sh
hatch run linkml-auto-converted:python \
  .claude/skills/dandi-linkml-validation-report/scripts/fetch_metadata.py \
  $ROOT/data
```

Downloads `metadata.json` + `info.json` for every dandiset's draft and
every published version into `$ROOT/data/<dandiset-id>/<version-or-draft>/`.
Already-downloaded versions are skipped. `--refresh` is a forceful
override that re-downloads everything regardless. `--limit N`
truncates to N dandisets for smoke tests. `-i <instance>` selects a
non-production DANDI instance.

### 2. Migrate + validate

```sh
hatch run linkml-auto-converted:python \
  .claude/skills/dandi-linkml-validation-report/scripts/validate_metadata.py \
  $ROOT/data --schema dandischema/models.yaml
```

For each version directory, runs `dandischema.metadata.migrate` on
the raw metadata first, then validates the migrated instance against
the LinkML schema (drafts → `Dandiset`, published → `PublishedDandiset`).
Writes `metadata_migrated.json` (when migration succeeds), plus
`validation.json` (structured record carrying `migration_status` and
`schema_sha256`), `validation.txt`, and `SUMMARY.md`. Versions whose
migration fails are recorded with the error and skipped for
validation.

The resume guard is schema-aware: each `validation.json` is stamped
with the SHA-256 of the schema file's bytes, and a re-run skips a
version only when its stamp matches the current schema. So changing
`dandischema/models.yaml` (committed or uncommitted) automatically
re-runs migration and validation for every version on the next call —
no flag needed. `--refresh` is a forceful override that ignores the
stamp and re-runs everything regardless.

### 3. Generate report

```sh
hatch run linkml-auto-converted:python \
  .claude/skills/dandi-linkml-validation-report/scripts/generate_report.py \
  $ROOT \
  --commit-hash $(git rev-parse linkml-auto-converted) \
  --commit-date $(git show -s --format=%cI linkml-auto-converted)
```

Writes `$ROOT/README.md`: overall counts, then per-bucket tables
(target class × schemaVersion) with top error patterns and links to
each version's `SUMMARY.md`. Always rewritten on invocation.

For details on the on-disk layout, JSON field shapes, and design
rationale, read the module docstrings of the three scripts directly.
