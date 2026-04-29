# Design notes

Rationale for non-obvious choices in the pipeline. Read this when you're
modifying a script and want to know why something was done a particular
way; the SKILL.md and OUTPUT.md cover the *what*.

## LinkML Python API, not the CLI

`validate_metadata.py` drives the `linkml.validator.Validator` class
directly rather than shelling out to `linkml-validate`. Reasons:

- One validation run produces both the structured `validation.json`
  and the human-readable `validation.txt`. Shelling out would force
  either a second run or downstream regex parsing of CLI text.
- `linkml-validate` has no JSON output flag (verified against the
  installed `linkml/validator/cli.py`), and its `--config` only
  externalizes the same arguments — there is no formatter knob.
- Subprocess overhead is meaningful when iterating ~900 dandisets
  with a few thousand version directories.

`Validator` is constructed once and reused across every version
directory; schema parsing is the expensive part.

## Closed-world JSON-schema plugin

We pass `JsonschemaValidationPlugin(closed=True)` when constructing the
validator. That matches the CLI's default (`{"JsonschemaValidationPlugin":
{"closed": True}}` in `linkml/validator/cli.py`), so the results we
collect are the same ones `linkml-validate` would emit.

`closed=True` causes LinkML to emit `additionalProperties: false` in
the generated JSON Schema — extra keys on a class become validation
errors. Switching to `closed=False` would silently accept unknown
fields and mask real bugs (e.g. `includeInCitation` on `Affiliation`),
so it's not an acceptable knob for "ignore one specific extra key".

## `@context` is stripped before validation

DANDI metadata carries a top-level JSON-LD framing key (`@context`)
that isn't part of the `Dandiset` / `PublishedDandiset` LinkML class
definitions. With `closed=True` it shows up as an
`additionalProperties` violation — see linkml/linkml#3442.

We `raw.pop("@context", None)` on the loaded dict before passing it to
`validator.validate(...)`. Cheap, local to the validator step, and
doesn't touch the saved `metadata.json` (which we keep verbatim).
Considered alternatives:

- Open up `closed=False` globally — too broad; loses signal.
- Post-validation filter — runs the validator, gets a known-noise
  result, throws it away. Backwards from intent.
- Custom plugin subclass — tracking LinkML internals just to skip one
  message; not worth it.
- Schema patch in `models.yaml` — `models.yaml` is auto-generated from
  `dandischema.models`, so the change would have to live in the
  Pydantic source. Too far away from the narrow concern.

## CLI byte-equivalent transcript

`validation.txt` is rendered by formatting each `ValidationResult`
with the same f-string `linkml-validate` uses
(`linkml/validator/cli.py`):

```
[<severity>] [<source-label>/<instance_index>] <message>
```

Plus a single-line `No issues found` when zero results, plus an
`exit_code` field in the JSON header that mirrors the CLI's exit code
(1 iff any `ERROR` severity is present, else 0). We interpolate
`r.instance_index` directly with no fallback so a `None` (which would
appear if LinkML stops emitting `0` for non-list instances) renders as
the literal `"None"` — same as the CLI. Today the JSON-schema plugin
always emits `0` for our single-instance `validate(raw, ...)` calls,
so the field renders as `0` in practice.

## Structured problem records

`validation.json` does *not* persist the CLI text and ask the report
to parse it. Each problem is the dict-form of a `ValidationResult`
plus the bits of `source` that matter for grouping
(`source.validator`, `source.validator_value`).

`source` is excluded from default pydantic serialization (it's a
plugin-defined object), so `_result_to_dict` extracts those two
attributes by hand. The `instance` field — which echoes the full data
instance back into every result — is excluded to avoid duplicating
`metadata.json` per problem.

`generate_report.py` groups patterns by `[<severity>] <<validator>>
<message>`, drawing the validator keyword from the structured record.
That groups across dandisets without regex-scrubbing the per-file path
out of the CLI text, and surfaces the failing JSON-schema keyword
(e.g. `additionalProperties`, `enum`, `format`) directly in the
report.

## All-or-nothing fetch writes

`fetch_metadata.py` writes `metadata.json` and `info.json` together or
not at all. Mechanism:

1. Network calls first — `get_raw_metadata()` and `get_version()` both
   complete before any filesystem write.
2. Pre-render both JSON strings.
3. Write each to a `.tmp` sibling.
4. `os.replace(...)` each `.tmp` onto its final path.

`os.replace` performs the POSIX `rename(2)` syscall; either the
destination ends up at the new content or it stays as it was before.
That guarantee is what makes the resume guard correct: the next run
checks for *both* `metadata.json` and `info.json` and skips only if
both exist, so a process killed mid-fetch never leaves a half-written
file that the resume guard would mistake for completion. (Leftover
`.tmp` files are harmless cruft that the next successful fetch
overwrites.)

We considered a `try/except` around plain writes to the final paths.
That's strictly worse: a SIGKILL between writing `metadata.json` fully
and `info.json` partially leaves both files existing with `info.json`
truncated, and the resume guard would skip the retry. The temp+rename
pattern can't reach that state.

## Resume semantics

Each stage skips work it's already done:

- `fetch_metadata.py`: skip a version when both `metadata.json` and
  `info.json` exist, unless `--refresh`.
- `validate_metadata.py`: skip a version when `validation.json`
  exists and parses, unless `--refresh`. If it parses but is
  unreadable, log a warning and re-validate.
- `generate_report.py`: stateless; always rewrites `README.md` from
  whatever `validation.json` files are present.

Failures in either of the first two stages are caught at the version
level — one broken dandiset doesn't abort the run.
