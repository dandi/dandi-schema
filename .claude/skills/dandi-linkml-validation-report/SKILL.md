---
name: dandi-linkml-validation-report
description: Generate a Markdown report assessing how `dandischema/models.yaml` (the LinkML schema) validates against real DANDI Archive Dandiset metadata. Use when the user wants to assess schema fitness across the archive, investigate a class of validation failure across many dandisets, or compare before/after for a schema change. Covers fetching raw metadata for every dandiset (draft + every published version), running closed-world JSON-schema validation via the LinkML Python API, and aggregating per-version results into a top-level README.md bucketed by target class (Dandiset / PublishedDandiset) × schemaVersion.
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

Pick a short SHA of the schema commit to namespace the run:

```sh
SHA=$(git rev-parse --short=7 linkml-auto-converted)
ROOT=linkml-validation-reports/$SHA
```

### 1. Fetch metadata

```sh
hatch run linkml-auto-converted:python \
  .claude/skills/dandi-linkml-validation-report/scripts/fetch_metadata.py \
  $ROOT/data
```

Downloads `metadata.json` + `info.json` for every dandiset's draft and
every published version into `$ROOT/data/<dandiset-id>/<version-or-draft>/`.
Re-running is safe — already-downloaded versions are skipped unless
`--refresh` is passed. `--limit N` truncates to N dandisets for smoke
tests. `-i <instance>` selects a non-production DANDI instance.

### 2. Validate

```sh
hatch run linkml-auto-converted:python \
  .claude/skills/dandi-linkml-validation-report/scripts/validate_metadata.py \
  $ROOT/data --schema dandischema/models.yaml
```

For each version directory, runs LinkML's `Validator` Python API once
and writes `validation.json` (structured results), `validation.txt`
(byte-equivalent to `linkml-validate` CLI output), and `SUMMARY.md`.
Drafts are validated against `Dandiset`; published versions against
`PublishedDandiset`. `--refresh` re-validates already-validated
versions.

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
each version's `SUMMARY.md`.

For details on the on-disk layout, JSON field shapes, and design
rationale, read the module docstrings of the three scripts directly.
