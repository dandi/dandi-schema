# Django (dandi-archive backend role)

Topical role: the Django backend of [`dandi/dandi-archive`](https://github.com/dandi/dandi-archive).

Stacks on top of [`senior-developer.md`](senior-developer.md) — load both together.

## Scope

- Django models, views, serializers, and migrations that depend on `dandischema`'s generated Pydantic models.
- Server-side validation paths that consume `dandischema` (whether via Pydantic models or JSON Schemas).
- Verifying that the generated Pydantic from the LinkML schema is a drop-in replacement for the hand-written `dandischema.models` in this consumer (success criterion 2 — see [OVERVIEW](../../OVERVIEW.md#success-criteria)).

## Not in scope

- Vue frontend → see [`vue.md`](vue.md).
- LinkML schema authoring → see [`linkml.md`](linkml.md).
- `pydantic2linkml` internals → see [`linkml.md`](linkml.md).
- [`dandi/dandi-cli`](https://github.com/dandi/dandi-cli) (the other major Python consumer of generated Pydantic) — its own scope; cover it with the senior-developer baseline or split out a `dandi-cli.md` role file later if it accrues distinct concerns.

## What this role needs to know

> TODO — to be filled out. Sketch:
>
> - Where in the backend `dandischema` is imported and what it's used for (validation, serialization, response shaping).
> - The Django/Python version floor of `dandi-archive` and which Pydantic v2 features are in use.
> - Local dev story: how to launch the backend pointing at locally-edited `dandischema`, including with the `linkml-auto-converted`'s `models_linkml.py` swapped in.
> - Database-migration sensitivities — anything that would break if the generated Pydantic differs subtly from the hand-written one.

## References

External skill/agent definitions to **lift content from** (review for fit before adopting wholesale — these are community collections of varying quality):

- [`anthropics/skills`](https://github.com/anthropics/skills) — canonical reference for the `SKILL.md` format and frontmatter conventions.
- [`VoltAgent/awesome-claude-code-subagents` → `django-developer.md`](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/02-language-specialists/django-developer.md) — Django 4+ specialist covering REST APIs, async views, ORM optimization, admin patterns. Closest off-the-shelf match.
- [`ammohq/agents`](https://github.com/ammohq/agents) — described as a "Supreme Django + DRF + ORM + Pillow expert"; useful if dandi-archive uses DRF heavily (verify before relying).
- [`wshobson/agents`](https://github.com/wshobson/agents) — broader marketplace; check for backend / Django entries.

`dandi-archive`-specific references:

- TODO: link the repo's backend `README.md`, `CONTRIBUTING.md`, or `DEVELOPMENT.md` once a session actually exercises the backend locally.
