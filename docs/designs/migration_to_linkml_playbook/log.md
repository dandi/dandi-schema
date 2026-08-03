# Migration log

Append-only, dated. Raw observations, attempts, dead ends, partial wins. Don't over-curate — promote durable conclusions to `findings.md` once they're stable.

## Format

```
## YYYY-MM-DD — <short topic>

**Context:** what triggered this entry (which step in OVERVIEW.md, which branch).
**Observation / attempt:** what happened.
**Outcome:** what we know now, what's still open.
**Next:** concrete next move, if any.
```

---

<!-- Add new entries below, newest at the bottom. -->

## 2026-08-02 — `models_pydantic/` is not an original-Pydantic baseline

**Context:** verifying a regenerated `linkml-auto-converted` after merging `master` into `linkml-conversion` (Approach step 3).

**Observation / attempt:** the diff of `dandischema/models_pydantic/dandiset.json` against the previous run removed `linkml_meta` keys, which only `gen-pydantic` emits. Checking the pipeline explains it: `tools/linkml_conversion` performs the rename dance (`models.py` → `models_orig.py`, stub → `models.py`) *before* calling `tools/linkml_conversion_fromlinkml`, whose `pydantic2json` stage runs `tools/pubschemata.py`. That reaches the models through `from . import models` in `dandischema/metadata.py`, which by then resolves to the stub re-exporting `models_linkml`. `linkml_meta` is present in every run inspected, so this is long-standing rather than new.

**Outcome:** OVERVIEW.md was wrong in three places, all now corrected: `models_pydantic/*.json` is dandischema's own `publish_model_schemata` output over the **generated** models, not over the original ones. The `pydantic2json` script itself is neutral about which models it serializes — the ordering inside `linkml_conversion` is what decides. Consequence for Approach step 5: the "cheap structural diff" compares two *serializers* (`gen-json-schema` vs `model_json_schema`) over one LinkML schema, and never touched the hand-written models, so on its own it could not have substantiated success criterion 3. It is still worth running because `models_pydantic/` is the shape `dandi-archive` consumes.

**Next:** for a real parity baseline, diff against the published schemata at <https://github.com/dandi/schema> rather than anything the pipeline emits. Whether to also produce an original-Pydantic set inside the pipeline (running `pubschemata.py` before the rename dance) is open — it would duplicate what `dandi/schema` already publishes.
