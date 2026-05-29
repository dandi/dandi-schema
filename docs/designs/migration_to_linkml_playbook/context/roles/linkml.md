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

> TODO — to be filled out. Sketch:
>
> - Pydantic v2 features that have no faithful LinkML equivalent (discriminated unions, custom validators, `Annotated` metadata) and the current workaround for each.
> - The exact semantic distinction between `-M` (`models_merge.yaml`) and `-O` (`models_overlay.yaml`) in `pydantic2linkml`'s CLI — currently described loosely in [OVERVIEW](../../OVERVIEW.md#how-the-translation-is-wired-today) ("corrections" vs. "merges") and worth tightening here against `pydantic2linkml`'s own docs.
> - LinkML schema conventions used by the rest of the dandi ecosystem (uri/CURIE schemes, identifier prefixes, range types) so generated schema fits.
> - When to upstream a fix to `pydantic2linkml` vs. when to patch via overlay/merge — heuristic recap from procedure step 7.

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
