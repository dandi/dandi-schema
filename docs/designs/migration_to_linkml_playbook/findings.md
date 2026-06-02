# Findings

Distilled, durable conclusions promoted out of `log.md`. A future attempt should read this **before** the log — these are the things we trust.

Each finding should answer: **what is true, how do we know, and what does it imply for the migration?**

## Format

```
### <Short claim, stated as a fact>

- **Evidence:** how we established this (link to log entry / commit / test).
- **Implication:** what this changes about the procedure or where to fix things.
- **Confidence:** high / medium / low — and what would lower it.
```

---

### `designates_type: true` makes generated artifacts resolve a superclass-typed slot value to its concrete subtype

- **Evidence:** the runnable exhibit [`tools/type-designator-demo/`](tools/type-designator-demo/) (see its `README.md`). Two minimal LinkML schemas differ only in whether `schemaKey` is `designates_type: true`. With the designator on, both generators key the slot on `schemaKey` and expand a multivalued `Activity`-ranged slot over its descendants: `gen-pydantic` emits `Optional[list[Union[Activity, Project]]]` with `schemaKey: Literal["<Class>"]`, and `gen-json-schema` emits `items: anyOf[Activity, Project]` with `schemaKey: enum[...]`. Without it, the slot stays `list[Activity]` / `$ref: Activity` and a `Project` is downcast (Pydantic) or its subclass-only fields are rejected (both). `pydantic_demo.py` and `jsonschema_demo.py` assert the divergence on a shared `BareAsset` instance.
- **Implication:** to preserve behavioral parity (success criterion 1), the LinkML schema should mark `schemaKey` with `designates_type: true` so the generated artifacts encode each class's `schemaKey` as a class-name literal (Pydantic `Literal`, JSON Schema `enum`) and can validate a data instance against — and identify it as — its concrete class. This is the `schemaKey`-based instance typing `dandischema` relies on today. It is **separate** from the `remove-discriminated-unions` patch-queue branch: that branch exists because `pydantic2linkml` cannot translate Pydantic *discriminated unions* in the source models into LinkML (no equivalent construct); `designates_type` is not a replacement for discriminated unions.
- **Confidence:** high. Verified end-to-end through both generators, including `schemaKey` edge cases: with the designator on, `schemaKey` is pinned to the class name — `valid`/`absent` accepted, `null`/`wrong-class` rejected — **identically** in Pydantic and JSON Schema (note `null` is rejected by the JSON Schema `enum` even though `type` lists it; there is no JSON-Schema-vs-Pydantic asymmetry). The `subtype_resolution/` and `schemakey_validation/` demo groups under the exhibit assert both findings. Verified with the `linkml-auto-converted` pipeline env (`linkml` 1.11.1); also confirmed on `linkml` 1.10.0.

### LinkML's `gen-json-schema` emits draft 2019-09; Pydantic and the dandi-archive frontend are both on 2020-12 — but the frontend strips `$schema`, so the gap is mostly cosmetic except for tuple arrays

- **Evidence:**
  - **LinkML → 2019-09, not configurable.** `gen-json-schema` hardcodes `"$schema": "https://json-schema.org/draft/2019-09/schema"` as a literal in `start_schema()` — `packages/linkml/src/linkml/generators/jsonschemagen.py:439` (local checkout `v1.11.0-27-gd24624c32`). No CLI flag or generator setting overrides it.
  - **Pydantic → 2020-12.** `pydantic.json_schema.GenerateJsonSchema.schema_dialect == "https://json-schema.org/draft/2020-12/schema"`, and dandischema's `TransitionalGenerateJsonSchema` (`dandischema/utils.py:71-86`) explicitly writes that into `$schema`; `publish_model_schemata` (`dandischema/metadata.py:133-147`) uses it to emit the published `*.json` schemata. So the Pydantic-derived baseline declares 2020-12.
  - **Frontend → Ajv 2020-12, but deletes `$schema` first.** `web/src/components/Meditor/utils.ts:3` imports `Ajv from 'ajv/dist/2020'` (the draft-2020-12 build; validator at `utils.ts:120`, form renderer `@koumoul/vjsf` 3.12.0). But `computeBasicSchema` does `delete newSchema.$schema` (`utils.ts:35-36`, comment: "$schema isn't needed and causes Ajv to throw an error"), so the declared dialect string never reaches Ajv — Ajv-2020 interprets whatever structure it's given with 2020-12 semantics regardless of the generator's declaration.
- **Implication:**
  - The LinkML-derived JSON Schema will diverge from the Pydantic baseline on at least the `$schema` line — a **guaranteed hit in the structural JSON-schema diff** (criterion 3). Expect it; don't treat it alone as a behavioral failure.
  - For the **frontend** specifically, the dialect mismatch is mostly cosmetic *because the frontend strips `$schema`* — but only as long as the schema contains no **tuple-typed arrays**. 2019-09 validates tuples with `items: [schemaA, schemaB]` + `additionalItems`; 2020-12 moved that to `prefixItems` + `items`. If LinkML ever emits the 2019-09 tuple form, Ajv-2020 silently mis-validates it. LinkML's `gen-json-schema` normally emits `items: {single schema}` for multivalued slots, which is identical in both drafts, so typical output is unaffected — tuples/`prefixItems` are the place to watch. (2019-09's `$recursiveRef`/`$recursiveAnchor` vs 2020-12's `$dynamicRef`/`$dynamicAnchor` don't apply — LinkML doesn't emit them; `$defs`/`$ref` are the same in both.)
  - **Clean fixes** if exact parity on the dialect is wanted: either a post-processing step on `models_linkml/*.json` (rewrite `$schema` to 2020-12, and convert any `items: [list]` → `prefixItems`), or an upstream patch (linkml's `jsonschemagen`, or `pydantic2linkml` which we own). Default per the playbook: upstream first.
- **Confidence:** high for the three dialect facts (all read directly from source). Medium on "mostly cosmetic for the frontend" — it rests on the current `delete $schema` behavior and on the schema staying free of tuple arrays; either changing would reopen it. Connects to the OVERVIEW open question about whether the frontend relies on JSON Schema extensions `gen-json-schema` doesn't emit.
