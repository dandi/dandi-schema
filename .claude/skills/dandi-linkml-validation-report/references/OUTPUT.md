# Output anatomy

Reference for the on-disk layout produced by the three pipeline stages
and the shape of every JSON artifact. The top-level `SKILL.md` describes
*how* to run the pipeline; this file describes *what it produces*.

## Directory layout

```
linkml-validation-reports/<short-sha>/
├── README.md                              # written by generate_report.py
└── data/
    └── <dandiset-id>/                     # e.g. 000003
        ├── draft/                         # draft version
        │   ├── metadata.json              # written by fetch_metadata.py
        │   ├── info.json                  # written by fetch_metadata.py
        │   ├── validation.json            # written by validate_metadata.py
        │   ├── validation.txt             # written by validate_metadata.py
        │   └── SUMMARY.md                 # written by validate_metadata.py
        └── <published-version-id>/        # e.g. 0.230629.1955
            └── …                          # same five files
```

`<short-sha>` is whatever the caller of `generate_report.py` passed for
`--commit-hash` (typically `git rev-parse --short=7 linkml-auto-converted`).
The pipeline doesn't inspect or enforce it — it's just a namespace for
the run.

## `metadata.json`

Verbatim raw metadata as returned by `RemoteDandiset.get_raw_metadata()`.
Pretty-printed JSON. Not modified after the fetch — every downstream
consumer reads this as the authoritative archive payload.

## `info.json`

Side-car written alongside `metadata.json` so the validator and the
report can pick the right target class and group records without
re-querying the archive.

```json
{
  "dandiset_id":    "000003",
  "version":        "0.230629.1955",
  "is_published":   true,
  "status":         "VALID",
  "modified":       "2023-06-29T19:55:35.080882+00:00",
  "schema_version": "0.6.4"
}
```

| Field            | Source                                               |
|------------------|------------------------------------------------------|
| `dandiset_id`    | `RemoteDandiset.identifier`                          |
| `version`        | Version id, or the literal string `"draft"`          |
| `is_published`   | `False` for the draft version, `True` otherwise      |
| `status`         | `version_info.status.value` (DANDI `VersionStatus`)  |
| `modified`       | `version_info.modified.isoformat()` (always present) |
| `schema_version` | `metadata["schemaVersion"]` (may be `null`)          |

`metadata.json` and `info.json` are written all-or-nothing: each is
written to a `.tmp` sibling first, then `os.replace`'d into place. If
the fetch is killed mid-write, neither final path appears, so the
resume guard treats that version as unfetched.

## `validation.json`

Structured validation record written by `validate_metadata.py`. One
record per version directory:

```json
{
  "dandiset_id": "000003",
  "version": "draft",
  "is_published": false,
  "target_class": "Dandiset",
  "schema_version": "0.6.0",
  "exit_code": 1,
  "problem_count": 3,
  "problems": [ { … }, … ]
}
```

Each entry in `problems` is a JSON-friendly serialization of one
LinkML `ValidationResult`:

```json
{
  "type": "jsonschema validation",
  "severity": "ERROR",
  "message": "'Dandiset' is not one of ['PublishedDandiset'] in /schemaKey",
  "instance_index": 0,
  "instantiates": "PublishedDandiset",
  "context": [],
  "source": {
    "validator": "enum",
    "validator_value": ["PublishedDandiset"]
  }
}
```

Notes on the fields:

- `instance` (the full data instance the validator was given) is
  excluded — it would duplicate `metadata.json` per problem and bloat
  the file. Look at the sibling `metadata.json` if you need the
  payload.
- `source.validator` / `source.validator_value` come from the
  `JsonschemaValidationPlugin` and identify the failing JSON-schema
  keyword (e.g. `additionalProperties`, `enum`, `format`,
  `required`). The report generator groups patterns by this field so
  similar failures across dandisets count together.
- `exit_code` is `1` if any `ERROR`-severity result is present, else
  `0` — matches `linkml-validate`'s exit-code semantics.

## `validation.txt`

Byte-equivalent to what `linkml-validate -s <schema> -C <target-class>
<metadata.json>` would have printed. Each line:

```
[<severity>] [<source-label>/<instance-index>] <message>
```

When there are zero results, the file contains the single line
`No issues found` (matching the CLI's success banner). The literal
text comes from re-formatting `ValidationResult` objects — we don't
shell out to the CLI.

## `SUMMARY.md`

Per-version markdown summary linked from the top-level report. Header
lists target class, archive status, modified timestamp, raw
`schemaVersion`, equivalent CLI exit code, and problem count; body
inlines up to the first 20 problem lines and links back to the raw
files.

## `README.md`

Top-level report written by `generate_report.py`.

Header:

- Branch name (default `linkml-auto-converted`)
- Commit hash + ISO commit date (passed in via flags)
- Schema path (default `dandischema/models.yaml`)
- Total versions and overall valid/with-problems count

Then one section per target class:

1. `Draft versions (target class: Dandiset)`
2. `Published versions (target class: PublishedDandiset)`

Each section is sub-bucketed by `schemaVersion` (newest first;
`<unknown>` last when present). Each sub-bucket contains:

- A one-line headline (versions / valid / failing)
- Top-N grouped problem patterns of the form
  `[<severity>] <<validator-keyword>> <message>` with counts
- A per-version table: `Dandiset | Version | Problems | API Status |
  Modified`, where `Problems` links to each version's `SUMMARY.md`.

The "API Status" column is the per-version `status` field that DANDI's
own API returns (`VALID`, `Published`, `Pending`, etc.) — not anything
the LinkML validator computed.
