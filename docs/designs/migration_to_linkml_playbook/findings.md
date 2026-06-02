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
