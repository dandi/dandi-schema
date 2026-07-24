# LinkML (schema authoring + translation pipeline role)

Topical role: the LinkML schema itself, and the Pydantic↔LinkML translation pipeline. Covers the core of the migration's source-of-truth flip.

Stacks on top of [`senior-developer.md`](senior-developer.md) — load both together.

## Scope

- Authoring and reviewing `dandischema/models.yaml` and its inputs (`dandischema/models_overlay.yaml`, `dandischema/models_merge.yaml`).
- The [`pydantic2linkml`](https://github.com/dandi/pydantic2linkml) translator. Owned by the DANDI team; systematic translation gaps are typically fixed here.
- LinkML generators in the pipeline: `gen-pydantic` (via the `2pydantic` Hatch script) and `gen-json-schema` (via `2json`).
- The Pydantic-template customization point at `tools/linkml_conversion_tools/pydantic_templates/`.
- The contract tests under `tests/linkml_behavior/` — pinning specific LinkML upstream behaviors the generated schema relies on (see [issue #405](https://github.com/dandi/dandi-schema/issues/405) for an example).
- Choosing where a fix lands (translator vs. overlay vs. merge vs. Pydantic source) — see [procedure step 7](../../OVERVIEW.md#approach--repeatable-procedure).

## Not in scope

- Vue frontend behavior driven by the generated JSON Schema → see [`vue.md`](vue.md).
- Django backend behavior driven by the generated Pydantic → see [`django.md`](django.md).

## What this role needs to know

### `-M` vs `-O` semantics (verified against `pydantic2linkml`'s source — `tools.py:770–809`)

This was an open question in OVERVIEW. The README's one-liner ("values from the file win on conflict") oversimplifies; the implementation is more nuanced:

- **`-M` / `--merge-file`** = **deep merge** via [`deepmerge.always_merger`](https://deepmerge.readthedocs.io/). Per-type strategy:
  - **dict** → **recursive deep merge** (descend; the file does *not* override the whole dict).
  - **list** → **append** the file's list to the existing one (the file does *not* override the whole list; items accumulate).
  - **set** → **union**.
  - **type mismatch** (file's value has a different type than the existing) → **file wins**.
  - **scalar** (int, str, bool, None) → **file wins**.
  - Result is validated against the LinkML meta schema.
- **`-O` / `--overlay-file`** = **shallow merge** of the YAML file into the generated schema (top-level keys only). Result is validated against the LinkML meta schema.

In this repo: `dandischema/models_merge.yaml` is the `-M` input, `dandischema/models_overlay.yaml` is the `-O` input.

Picking between them:

- **Use `-M` (deep merge)** when overriding a *scalar* deep inside the generated structure (e.g. flipping a `required: false` to `true` on a specific slot) or adding items to a list (e.g. extra `permissible_values` on an enum, extra slots on a class). Items accumulate; nested dicts merge.
- **Use `-O` (shallow merge)** when patching at the top of the document — adding/replacing whole top-level keys like extra classes, slots, enums, or prefixes — and you do *not* want the merge to descend.

Honest gotcha: because `-M` **appends** lists rather than replacing them, you cannot remove or reorder items via `-M` alone. If you need to *replace* a list outright, either switch to `-O` (if the list is top-level) or change the source on the Pydantic side. When in doubt, run the conversion with a minimal patch and diff the resulting `models.yaml` — cheaper than guessing.

### How `pydantic2linkml` actually works

From `pydantic2linkml/CLAUDE.md`: it translates Pydantic v2 models by **introspecting Pydantic's internal `core_schema` objects**, not the higher-level model API. Two consequences:

- The translation is sensitive to **how Pydantic v2 builds its `core_schema`** for a given construct. Changes to `dandischema.models` that look semantically identical may yield different `core_schema` shapes and therefore different LinkML output.
- The translation can be sensitive to **the Pydantic version itself**. `pydantic2linkml`'s test matrix runs Python 3.10–3.13 and includes `dandischema` and `aind-data-schema` as known consumers. Bumping Pydantic upstream may require a matching `pydantic2linkml` adjustment before the dandischema migration sees green again.

### `pydantic2linkml` conventions (lifted from its `CLAUDE.md`)

When upstreaming a fix:

- **Hatch is the env manager.** Test invocations: `hatch run test.py3.10:pytest tests/`, type-check with `hatch run types:check`, lint/format with `ruff check . && ruff format .`, spell-check with `codespell`.
- **Document-currency rule** (mirrors this playbook's self-updating rule): "Whenever you notice that any documentation — `CLAUDE.md`, `README.md`, or any other docs — is outdated or incorrect, update it immediately."
- **Prose wraps at ~79 characters** in docs (code blocks and long URLs exempt). Match this when editing markdown there.

### LinkML upstream conventions (lifted from `linkml/linkml/AGENTS.md`)

When working in or proposing changes to `linkml/linkml`:

- **`uv run`** prefix on every command (UV-workspace monorepo publishing both `linkml` and `linkml-runtime`).
- **Pytest functional style, never `unittest`-OO style.** Modern idioms: `@pytest.mark.parametrize` for combinations.
- **Doctests are first-class** — both explanatory examples and unit tests. For longer cases, write pytest tests.
- **Never mock** unless explicitly requested. *"I need to rely on tests to know if something breaks."*
- **Never weaken a failing test** to make it pass — try harder or ask.
- **Avoid `try/except` that masks bugs.** Fail fast.
- **Always use type hints; always document methods and classes.**
- For tests with external dependencies, use the `integration` pytest mark.

### Pydantic-v2 features with no faithful LinkML equivalent (current state)

These are the recurring trouble spots:

- **Discriminated unions** — no LinkML equivalent; currently worked around by the `remove-discriminated-unions` patch-queue branch (see [`patch-queue.md`](../patch-queue.md)). Exit criterion is either an upstream `pydantic2linkml` improvement or an acceptable assessment of the frontend impact (see [`vue.md`](vue.md)).
- **Custom `@field_validator` / `@model_validator` decorators** — runtime-only behavior; LinkML's static schema can't carry the validator code itself. Watch for accuracy gaps where Pydantic accepts/rejects something the JSON Schema doesn't.
- **`Annotated[..., FieldInfo(...)]` and rich `Field()` metadata** — depending on which metadata is set, the translation may or may not faithfully round-trip. Verify by re-generating Pydantic from the LinkML and diffing against the source.
- **`model_config` knobs** (e.g. `populate_by_name`, JSON-serialization aliases) — easy to forget that these change Pydantic behavior in ways LinkML can't represent declaratively.

### The two downstream consumers' Pydantic pinning

- `dandi-archive` pins `dandischema==0.12.1` (exact; schema version 0.7.0).
- `dandi-cli` pins `dandischema ~= 0.12.0` (compatible-release).
- The generated Pydantic must remain importable and behaviorally equivalent for both. See [`django.md`](django.md) for the backend's import sites and [the migration's success criteria](../../OVERVIEW.md#success-criteria).

### Decision matrix for "where to fix" (refines [procedure step 7](../../OVERVIEW.md#approach--repeatable-procedure))

| Symptom | First place to look | Likely fix layer |
|---|---|---|
| Whole class of Pydantic constructs translates wrong | `pydantic2linkml`'s `core_schema` introspection | **Upstream `pydantic2linkml`** |
| One generated class/slot has a specific wrong value | Compare `models.yaml` against `models.py` for that class | **`models_merge.yaml`** (`-M`, file-wins deep merge) |
| Need to add a top-level element (class, enum, prefix) not in the source | Inspect generated `models.yaml` structure | **`models_overlay.yaml`** (`-O`, shallow merge) |
| The Pydantic source itself is under-specified or wrong | `dandischema/models.py` | **`dandischema/models.py`** on `linkml-conversion` |
| Generated Pydantic differs subtly from intent | `tools/linkml_conversion_tools/pydantic_templates/` | **Customize the Jinja templates** consumed by `gen-pydantic` in `2pydantic` |

Default preference, in order: upstream `pydantic2linkml` > source Pydantic > merge/overlay > template customization. Reach for the lower-leverage tool only when the higher-leverage one can't cleanly express the change.

## References

**First-party LinkML AI guidance (read these first):**

- [`linkml/linkml/AGENTS.md`](https://github.com/linkml/linkml/blob/main/AGENTS.md) (symlinked from `CLAUDE.md`) — maintainer-authored "Claude Code Notes for LinkML." Covers the UV-workspace monorepo layout (`linkml` and `linkml-runtime` published from one repo), the mandatory `uv run` prefix, and Best Practices that are directly applicable here: prefer doctests + pytest functional style, never mock tests, never weaken failing tests, avoid try/except masking bugs, fail fast, always use type hints. When working inside `linkml/linkml` (or proposing changes upstream), this file's rules supersede generic instincts.
- [`linkml/linkml/.claude/skills/codecov-coverage/SKILL.md`](https://github.com/linkml/linkml/blob/main/.claude/skills/codecov-coverage/SKILL.md) — a real first-party LinkML `SKILL.md`. Useful as a structural example (frontmatter, `allowed-tools`, "When to Use" section, coverage-decrease rule) when this role file is promoted to a skill. The skill itself is about Codecov, not topical LinkML — but the *form* is exemplary.

Primary sources:

- [LinkML specification](https://w3id.org/linkml/specification) — the normative spec; the source of truth for what LinkML means, ahead of any tutorial-style docs.
- [LinkML official docs](https://linkml.io/linkml/) — schema syntax, generators (`gen-pydantic`, `gen-json-schema`), runtime.
- [`linkml/linkml`](https://github.com/linkml/linkml) on GitHub.
- [`linkml/linkml-runtime`](https://github.com/linkml/linkml-runtime).
- [`dandi/pydantic2linkml`](https://github.com/dandi/pydantic2linkml) — the translator we own. README, open issues, and source are the authoritative description of `-M`/`-O` semantics and current translation gaps.

In-tree reference:

- [`.claude/skills/dandi-linkml-validation-report/SKILL.md`](https://github.com/dandi/dandi-schema/blob/linkml-auto-converted/.claude/skills/dandi-linkml-validation-report/SKILL.md) on the `linkml-auto-converted` branch — a working `SKILL.md` already tied to this migration. Useful as a local example of how a LinkML-flavored skill is shaped.

Format reference:

- [`anthropics/skills`](https://github.com/anthropics/skills) — canonical `SKILL.md` format, if/when this role file is promoted to an actual skill.

**Not yet checked:** other repos in the [`linkml` GitHub org](https://github.com/linkml) (`schema-automator`, `linkml-model`, `linkml-validator`, `linkml-store`, `linkml-project-cookiecutter`, etc.) may also carry AGENTS.md / `.claude/skills/` content. Worth spot-checking when scope expands beyond the two clones we have locally.
