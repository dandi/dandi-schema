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

## 2026-08-06 — stale `MANUAL_NOTE` merge entries produced phantom classes

**Context:** verifying that dandi/dandi-schema#407 could be closed, on `linkml-auto-converted` at `e2cadb78` (the regeneration that first included dandi/dandi-schema#419), then acting on the remaining `MANUAL_NOTE` sub-task of dandi/dandi-schema#389 on `linkml-conversion`.

**Observation / attempt:** #407 checks out: `dandischema/models.yaml` carries no `Cannot express in a slot_usage entry` note at all, and none of the three `Removal` rules in `tools/linkml_conversion_tools/remove_notes_by_pattern.py` could have masked one, so the absence is genuine rather than sanitized away. The cause is #419 consolidating `PublishedDandiset` into `Dandiset`, which leaves nothing to override the inherited `id` pattern. While confirming this, the three `MANUAL_NOTE` entries in `dandischema/models_merge.yaml` turned out to be stale for two different reasons. `BareAsset` is a genuine resolution: its `schemaKey` default is now `"BareAsset"`. `PublishedAsset` and `PublishedDandiset`, by contrast, are no longer classes at all, only module-level aliases, so `pydantic2linkml` emits nothing for them and the deep merge *creates* the keys instead of annotating them. The visible damage was two note-only classes in `models.yaml` and two empty `ConfiguredBaseModel` subclasses in the generated `dandischema/models_linkml.py`.

**Outcome:** all three entries removed. A merge entry is only ever a *modifier* of generated output when the corresponding element is actually generated; where it is not, `-M` silently manufactures the element. That makes a merge entry naming a class that no longer exists a schema-corrupting leftover, not a harmless one, and it is invisible in the merge file itself. `tools/linkml_conversion_tools/find_schemakey_mismatches.py` was also misleading here: it enumerates module attributes, so aliases surfaced as mismatches. It now skips an attribute whose name differs from the class's own name when that class is also reachable under its own name, and its `LAST_SCHEMAKEY_MISMATCHES` baseline is empty, which is the post-#419 truth.

**Next:** re-run `./tools/linkml_conversion` and confirm the two phantom classes disappear from `models.yaml` and `models_linkml.py`. More generally, when a class disappears from `dandischema/models.py`, check `models_merge.yaml` for entries naming it in the same change.

## 2026-08-07 — correction: the phantom `Published*` classes were load-bearing

**Context:** re-running `./tools/linkml_conversion` after the previous entry's cleanup, which produced `0ce51b35` on `linkml-auto-converted`.

**Observation / attempt:** the run failed. `2json` warned `No class in schema named PublishedAsset`, then `pydantic2json` died with `AttributeError: module 'dandischema.models' has no attribute 'PublishedDandiset'`. Two stages had been depending on the phantom classes without anyone noticing: the `2json` target list in `pyproject.toml` named all four classes, and `publish_model_schemata` resolves every `metadata.SCHEMA_MAP` key with `getattr(models, class_)`, which on `linkml-auto-converted` goes through the import stub to `models_linkml`. The empty classes had been satisfying both lookups. Note the two stages fail for unrelated reasons: `2json` reads `dandischema/models.yaml`, so the rename dance preceding it is irrelevant, whereas `pydantic2json` is the only stage the rename actually affects.

**Outcome:** the previous entry's claim that the entries were purely harmful leftovers was incomplete, and the phantom-class removal turned out to be a net improvement rather than only a cleanup. `models_linkml/published-*.json` had been rootless schemas all along (`properties: 0`, `additionalProperties: true`, so they accepted any object), and `models_pydantic/published-*.json` had been generated from the *empty* phantom classes. Dropping the two `2json` targets (`7ed984e9`) removes the former, and adding the aliases to the stub (`54138ad3`, tracked for removal in #439) makes the latter resolve to the real models: they are now byte-identical to `asset.json` and `dandiset.json`, which is what #419 predicted. The phantoms were also emitted into every `$defs` block, so `models_linkml/{dandiset,asset}.json` shed them too (52 → 50 defs).

**Next:** when removing a class from the generated schema, grep the pipeline for hardcoded class-name lists as well as `models_merge.yaml`. The two known ones are the `2json` loop in `pyproject.toml` and `SCHEMA_MAP` in `dandischema/metadata.py`.
