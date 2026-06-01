# type-designator-demo

A self-contained, runnable exhibit showing that LinkML's **`designates_type: true`**
makes the generated Pydantic models and JSON Schema resolve a value in a
superclass-typed slot to its concrete subtype, instead of flattening it to the
declared supertype. It does this by encoding each class's `schemaKey` as a
class-name literal (a `Literal["<Class>"]` in Pydantic, an `enum` in JSON Schema),
so a data instance can be validated against — and identified as — its concrete
class. Relevant to behavioral parity (success criterion 1 in
[`../../OVERVIEW.md`](../../OVERVIEW.md)), since `dandischema` relies on
`schemaKey` to identify each instance's class.

## Layout

```
type-designator-demo/
├── schemas/                 shared sources + generated snapshots
├── subtype_resolution/      demo group: subtype resolution through a slot
└── schemakey_validation/    demo group: how schemaKey itself is validated
```

Two minimal LinkML schemas in `schemas/` differ only in how the `schemaKey` slot
is declared:

- **`schema_no_type_designator.yaml`** — `schemaKey` is a plain `string` whose
  per-class value is set via `ifabsent`.
- **`schema_type_designator.yaml`** — `schemaKey` is declared
  `designates_type: true`.

Both define the same hierarchy: `Activity` <- `Project` (which adds a
`Project`-only `project_name` slot), and `CommonModel` <- `BareAsset` with a
multivalued slot `wasGeneratedBy` ranged on `Activity`.

The `schemas/` directory also holds the **generated snapshots**
(`models_*.py`, `schema_*.json`), committed so the demos run without first
invoking the generators. Each demo group imports those modules / reads those
JSON Schemas from `../schemas/`.

## Finding 1 — subtype resolution (`subtype_resolution/`)

When the type designator is turned on, **both** generators expand the slot range
over the class's descendants and key it on `schemaKey`:

| representation | no type designator | type designator |
| --- | --- | --- |
| Pydantic `wasGeneratedBy` | `Optional[list[Activity]]` | `Optional[list[Union[Activity, Project]]]` |
| Pydantic `schemaKey` | `Optional[str]` (default per class) | `Literal["<Class>"]` |
| JSON Schema `wasGeneratedBy.items` | `$ref: Activity` | `anyOf: [Activity, Project]` |
| JSON Schema `schemaKey` | `type: [string, null]` | `enum: ["<Class>"]` |

So a `Project` placed in a `BareAsset.wasGeneratedBy` list is **only** correctly
recognized as a `Project` when the designator is on. The demos prove this with
the shared instance `bareasset_instance.json`, whose single `wasGeneratedBy` item
is a `Project` carrying `project_name`:

- `pydantic_demo.py` — the no-designator module **rejects** the instance
  (`Activity` forbids the extra `project_name`); the type-designator module
  resolves the item to a concrete `Project` and preserves `project_name`.
- `jsonschema_demo.py` — the no-designator JSON Schema marks the instance
  **invalid** (`additionalProperties: false` on `Activity`); the type-designator
  JSON Schema marks it **valid** (it matches the `Project` branch of the `anyOf`).

## Finding 2 — `schemaKey` validation (`schemakey_validation/`)

With `designates_type: true`, `schemaKey` is pinned to the class name; without
it, `schemaKey` is an unconstrained optional/nullable string. Crucially, the
type-designator constraint is enforced **identically** by Pydantic and JSON
Schema. The demos validate the four cases in `schemakey_cases.json` against
`BareAsset` from each variant:

| case (`schemaKey` value) | no type designator | type designator |
| --- | --- | --- |
| `"BareAsset"` (class name) | accepted | accepted |
| absent | accepted | accepted (default fills it in) |
| `null` | accepted | **rejected** |
| `"WrongClass"` | accepted | **rejected** |

Both `pydantic_demo.py` and `jsonschema_demo.py` assert the same table — there is
**no JSON-Schema-vs-Pydantic asymmetry**. Note the `null` case: the
type-designator `schemaKey` JSON Schema is
`{"enum": ["BareAsset"], "type": ["string", "null"]}`, and even though `type`
lists `null`, `null` is rejected because it is not in `enum` (JSON Schema requires
every keyword to pass) — matching Pydantic's `Literal["BareAsset"]`.

## Caveats

- The generated Pydantic union is a **plain `Union`**, not a Pydantic
  [discriminated union](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions)
  — there is no `Field(discriminator="schemaKey")`. It resolves correctly because
  each member's `schemaKey` is a distinct `Literal`, but it relies on Pydantic's
  smart-union matching rather than tagged-union dispatch.
- This is **orthogonal to the `remove-discriminated-unions` patch-queue branch.**
  That branch exists because `pydantic2linkml` cannot translate Pydantic
  discriminated unions in the *source* models into LinkML (no equivalent
  construct). `designates_type` is a separate feature — about `schemaKey`
  encoding for instance validation — and is not a replacement for discriminated
  unions.

## Files

`schemas/`

| file | role |
| --- | --- |
| `schema_no_type_designator.yaml` | source LinkML schema, `schemaKey` via `ifabsent` |
| `schema_type_designator.yaml` | source LinkML schema, `schemaKey` via `designates_type: true` |
| `models_no_type_designator.py` / `models_type_designator.py` | generated Pydantic (snapshots) |
| `schema_no_type_designator.json` / `schema_type_designator.json` | generated JSON Schema (snapshots) |

`subtype_resolution/`

| file | role |
| --- | --- |
| `bareasset_instance.json` | a `BareAsset` whose `wasGeneratedBy` holds one `Project` (with `project_name`) |
| `pydantic_demo.py` | asserts Finding 1 via Pydantic `model_validate` |
| `jsonschema_demo.py` | asserts Finding 1 via JSON Schema validation |

`schemakey_validation/`

| file | role |
| --- | --- |
| `schemakey_cases.json` | four `BareAsset` instances: valid / absent / null / wrong-class `schemaKey` |
| `pydantic_demo.py` | asserts Finding 2 via Pydantic `model_validate` |
| `jsonschema_demo.py` | asserts Finding 2 via JSON Schema validation |

## Running the demos

From the repo root, using the `linkml-auto-converted` Hatch env — the migration
pipeline env, which pins `linkml==1.10.0` (and provides `pydantic`, `jsonschema`,
and the LinkML CLIs). Running in the pipeline env keeps the demos consistent with
the LinkML version the migration actually generates against:

```sh
B=docs/designs/migration_to_linkml_playbook/tools/type-designator-demo
for d in subtype_resolution schemakey_validation; do
  hatch run linkml-auto-converted:python "$B/$d/pydantic_demo.py"
  hatch run linkml-auto-converted:python "$B/$d/jsonschema_demo.py"
done
```

Each prints `All assertions passed.` and exits 0; an assertion fires if the
behavior ever changes.

## Regenerating the snapshots

Run from inside `schemas/` so the generated `source_file` metadata stays
relative. `hatch` finds the project by walking up to the repo-root
`pyproject.toml`.

```sh
cd docs/designs/migration_to_linkml_playbook/tools/type-designator-demo/schemas
TPL=../../../../../../tools/linkml_conversion_tools/pydantic_templates
for v in no_type_designator type_designator; do
  hatch run linkml-auto-converted:gen-json-schema --title-from title "schema_${v}.yaml" > "schema_${v}.json"
  hatch run linkml-auto-converted:gen-pydantic --black --template-dir "$TPL" "schema_${v}.yaml" > "models_${v}.py"
done
```

The `gen-json-schema --title-from title` and
`gen-pydantic --black --template-dir <pydantic_templates>` invocations mirror the
migration pipeline's `2json` / `2pydantic` Hatch scripts (see
[`../../OVERVIEW.md`](../../OVERVIEW.md)).

## Provenance

Snapshots generated and demos verified with the `linkml-auto-converted` pipeline
env: `linkml` 1.10.0, `linkml-runtime` 1.10.0, `pydantic` 2.10.6, `jsonschema`
4.26.0. Using the pipeline env (rather than a detached one tracking the latest
`linkml`) keeps these snapshots consistent with what the migration actually
generates. The `designates_type` behavior was also confirmed on `linkml` 1.11.1.
