# schemaKey Mismatch Report

## Related issues and PRs

- [dandi/dandi-schema#389](https://github.com/dandi/dandi-schema/issues/389) --
  **Handle LinkML migration issue of `pydantic2linkml: Impossible to generate
  slot usage entry for the`** (open). The parent issue for this investigation.
  Documents 54 pydantic2linkml conversion errors, 41 of which concern
  `schemaKey` slot usage. Includes the open TODO items about figuring out why
  `schemaKey` differs from class name for Published/Bare models.
- [dandi/dandi-schema#388](https://github.com/dandi/dandi-schema/issues/388) --
  **Establish at least 8 issues for specific groups of problems in converted
  linkml** (open). Umbrella issue cataloguing all pydantic2linkml translation
  problems, grouped by category.
- [dandi/dandi-schema#385](https://github.com/dandi/dandi-schema/pull/385) --
  **Replace discriminated unions with simple unions in models** (open PR).
  Removes `Field(discriminator="schemaKey")` in favor of plain `Union[...]`,
  since LinkML has no discriminated union equivalent
  ([dandi/pydantic2linkml#39](https://github.com/dandi/pydantic2linkml/issues/39)).
  Each union member still has a distinct `schemaKey: Literal[...]`, so
  Pydantic's smart union mode resolves correctly without an explicit
  discriminator. Has a pending TODO to analyze effects on the Meditor.
- [dandi/dandi-schema#244](https://github.com/dandi/dandi-schema/issues/244) --
  **Use discriminated unions to improve validation errors** (closed). The
  original issue that introduced discriminated unions on `schemaKey` to improve
  validation error messages for `Union[Person, Organization]` contributor
  fields. Now being reversed by #385 for LinkML compatibility.
- [dandi/dandi-schema#205](https://github.com/dandi/dandi-schema/issues/205) --
  **Overhaul models so that "unfinished" metadata can be represented without
  cheating Pydantic** (open). Proposes separate draft vs published models so
  that draft metadata does not need `model_construct()` to bypass validation.
  Directly relevant to the Bare/Published model split that causes the schemaKey
  mismatch.
- [dandi/dandi-schema#77](https://github.com/dandi/dandi-schema/pull/77) --
  **make schemaKey required and improve validation and migration functions**
  (merged PR). Made `schemaKey` a required field in JSON Schema output and added
  validation logic.
- [dandi/dandi-schema#68](https://github.com/dandi/dandi-schema/pull/68) --
  **ensure schemaKeys are set properly** (merged PR). Early work to set up
  schemaKey defaults and validation across all models.
- [dandi/dandi-schema#13](https://github.com/dandi/dandi-schema/pull/13) --
  **Fix/schemakey metaclass** (merged PR). Original implementation of the
  schemaKey metaclass and the `enum` -> `const` conversion in JSON Schema
  export.

## Summary

Three pydantic model classes in `dandischema/models.py` have `schemaKey` values
that do not match their class name:

| Class              | schemaKey   | Expected          |
|--------------------|-------------|-------------------|
| `BareAsset`        | `"Asset"`   | `"BareAsset"`     |
| `PublishedDandiset` | `"Dandiset"` | `"PublishedDandiset"` |
| `PublishedAsset`   | `"Asset"`   | `"PublishedAsset"` |

(`Asset` inherits `"Asset"` from `BareAsset` and does match its class name, so
it is not a mismatch.)

## Why it was done this way

### 1. Deliberate validator logic

The `ensure_schemakey` validator (`models.py:570-582`) has explicit special-case
logic that compensates for the mismatch:

```python
if "Published" in cls.__name__:
    tempval = "Published" + tempval      # "Dandiset" -> "PublishedDandiset"
elif "BareAsset" == cls.__name__:
    tempval = "Bare" + tempval           # "Asset" -> "BareAsset"
if tempval != cls.__name__:
    raise ValueError(...)
```

This proves the mismatch was intentional, not accidental.

### 2. Conceptual collapsing in JSON Schema

When exporting to JSON Schema (`__get_pydantic_json_schema__`, line 659-664),
`schemaKey` is emitted as a `const`:

```python
if prop == "schemaKey":
    if "enum" in value and len(value["enum"]) == 1:
        value["const"] = value["enum"][0]
        del value["enum"]
    else:
        value["const"] = value["default"]
```

This means:
- `BareAsset`, `Asset`, `PublishedAsset` all produce `"schemaKey": {"const": "Asset"}`
- `Dandiset`, `PublishedDandiset` both produce `"schemaKey": {"const": "Dandiset"}`

The design intent was that from a JSON Schema / API consumer perspective, there
are only two top-level entity kinds: **Asset** and **Dandiset**. The
Bare/Published distinctions are Python model hierarchy implementation details.

## How schemaKey is used

### dandi-archive backend (`dandiapi/`)

1. **Validation** (`dandiapi/api/services/metadata/__init__.py`): The archive
   explicitly calls `validate(metadata, schema_key='PublishedAsset')` and
   `validate(..., schema_key='PublishedDandiset')` -- passing the **class name**
   as `schema_key`, not the schemaKey value. The `validate()` function in
   dandischema (`metadata.py:328`) uses the `schema_key` parameter to do
   `getattr(models, schema_key)` to look up the pydantic class directly. So the
   archive backend **bypasses schemaKey entirely** for choosing which model to
   validate against.

2. **Schema endpoint** (`dandiapi/api/views/schema.py`): Exposes JSON schemas
   for `Dandiset`, `Asset`, `PublishedDandiset`, `PublishedAsset` via
   `?model=<ClassName>`. The mapping uses `__name__` (class name), not
   `schemaKey`. So again, the model identity is carried by the Python class name,
   not by `schemaKey`.

3. **Default metadata construction** (`dandiapi/api/services/version/metadata.py`,
   `dandiapi/api/models/version.py`): When constructing default metadata dicts,
   the archive hardcodes `'schemaKey': 'Dandiset'` and `'schemaKey': 'Asset'`.
   It never writes `'PublishedDandiset'`, `'PublishedAsset'`, or `'BareAsset'`
   as schemaKey values.

4. **Metadata stripping** (`dandiapi/api/models/version.py:196-203`): The
   `strip_metadata` method explicitly strips `schemaKey` from `access` sub-objects,
   treating it as a computed/server-controlled field.

### dandi-archive frontend (Meditor)

1. **Schema fetching** (`web/src/stores/dandiset.ts:112-122`): The Meditor
   fetches the JSON Schema from the API endpoint
   (`/api/schemas/?model=Dandiset`). This returns the `Dandiset` model's JSON
   Schema where `schemaKey` has `"const": "Dandiset"`.

2. **Meditor types** (`web/src/components/Meditor/types.ts:41-48`): The type
   `SchemaKeyPropertiesIntersection` expects schemas to have:
   ```typescript
   schemaKey: {
     type: 'string';
     const: string;  // expects a const value
   };
   ```
   The Meditor treats `schemaKey` as a read-only const field. It does **not**
   use the schemaKey value to dispatch between different model types; it relies
   on the JSON Schema structure itself.

3. **Discriminator usage in Vue components**
   (`web/src/components/DLP/OverviewTab.vue`, `web/src/utils/cff.ts`): The
   frontend uses `schemaKey` to discriminate between `Person` and `Organization`
   in contributor lists, but this is among truly distinct types -- not among
   Bare/Published variants.

4. **VJSF rendering**: The Meditor uses VJSF (Vue JSON Schema Forms) which
   renders forms from JSON Schema. The `schemaKey` field's `const` constraint
   means it appears as a non-editable fixed value. The Meditor's `utils.ts`
   validates using Ajv against the schema, and the `const: "Dandiset"` constraint
   means submitted metadata must have `schemaKey: "Dandiset"`.

### dandi-cli

- `dandi-cli` uses `schemaKey` as a **discriminator** for pydantic tagged unions
  (e.g., `Field(discriminator="schemaKey")` at `models.py:1284` for
  `Union[Person, Organization, Software, Agent]`).
- In tests, `BareAsset` instances are constructed with `schemaKey="Asset"`.
- The `schemaKey` value `"Session"` vs `"Activity"` is used to filter
  `wasGeneratedBy` entries (`test_metadata.py:528`).

### dandischema validation (`metadata.py`)

- `SCHEMA_MAP` maps class names to JSON Schema files: `"Dandiset"` ->
  `"dandiset.json"`, `"PublishedDandiset"` -> `"published-dandiset.json"`, etc.
- `validate()` accepts an explicit `schema_key` parameter (class name). If not
  provided, it falls back to `obj.get("schemaKey")` -- and since stored objects
  have `schemaKey: "Dandiset"` (not `"PublishedDandiset"`), this fallback would
  select the wrong (base) model for Published variants.
- This is why dandi-archive always passes `schema_key='PublishedDandiset'`
  explicitly.

## Impact of making schemaKey match model name

### What would change

If `BareAsset.schemaKey` becomes `"BareAsset"`, `PublishedDandiset.schemaKey`
becomes `"PublishedDandiset"`, and `PublishedAsset.schemaKey` becomes
`"PublishedAsset"`:

1. **dandischema `ensure_schemakey` validator**: The special-case prefix logic
   can be removed -- each class simply checks `val == cls.__name__`.

2. **dandischema `validate()` fallback**: The `obj.get("schemaKey")` fallback
   path would now correctly resolve to the right model for Published variants.

3. **JSON Schema output**: Each model would emit its own unique `const` value,
   enabling true type discrimination in JSON Schema.

4. **dandi-archive backend**: Hardcoded `'schemaKey': 'Dandiset'` and
   `'schemaKey': 'Asset'` in metadata construction would need to stay as-is for
   draft versions (which use `Dandiset`/`Asset` models) but
   `PublishedDandiset`/`PublishedAsset` validation already passes `schema_key`
   explicitly so no change needed there.

5. **dandi-archive Meditor**: The schema endpoint returns the `Dandiset` model's
   schema (not `PublishedDandiset`), so `const: "Dandiset"` stays the same for
   the editor. No Meditor change needed.

6. **Existing published metadata**: All published dandiset metadata in the
   database has `schemaKey: "Dandiset"` and `schemaKey: "Asset"`. A migration
   would be needed to update existing records if we want consistency, or the
   Published models must accept both old and new values during a transition
   period.

### Benefits for LinkML

- `schemaKey` can serve as a proper **type designator** for deserialization
- Satisfies LinkML's **monotonic slot constraint** (each class gets a unique
  const, no conflicting overrides in slot_usage)
- Enables correct round-tripping: serialize -> schemaKey -> deserialize to the
  right class

### Risks

- **Data migration**: Existing records in the archive database and published
  metadata files contain `schemaKey: "Dandiset"` / `"Asset"` for what are
  actually `PublishedDandiset` / `PublishedAsset` instances. Any consumer that
  matches on the exact string would need updating.
- **Schema version boundary**: This is a semantic change that ideally coincides
  with a schema version bump.

## Recommendation

Making `schemaKey` match the model name is the correct path forward for the
LinkML migration. The current mismatch exists purely as a legacy design choice
that treats Bare/Published as invisible variants. In practice, the archive
backend already works around this by passing explicit `schema_key` parameters.
The Meditor is unaffected since it only deals with draft `Dandiset` metadata.

The change should be coordinated with a schema version bump and a data migration
plan for existing published records.
