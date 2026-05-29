# Vue (dandi-archive frontend role)

Topical role: Vue and the JSON-Schema-driven UI in [`dandi/dandi-archive`](https://github.com/dandi/dandi-archive).

Stacks on top of [`senior-developer.md`](senior-developer.md) — load both together.

## Scope

- The Vue components and form-generation machinery that consume `dandischema`'s generated JSON Schemas.
- Verifying that the LinkML-derived JSON Schema drives the frontend the same way the Pydantic-derived one does (success criterion 3 — see [OVERVIEW](../../OVERVIEW.md#success-criteria)).
- Driving the UI via Playwright MCP for the end-to-end parity check in [procedure step 5](../../OVERVIEW.md#approach--repeatable-procedure).

## Not in scope

- Django backend → see [`django.md`](django.md).
- LinkML schema authoring → see [`linkml.md`](linkml.md).
- `pydantic2linkml` internals → see [`linkml.md`](linkml.md).

## What this role needs to know

> TODO — to be filled out. Sketch of what belongs here once the GitHub-inspiration pass lands:
>
> - Where in `dandi-archive` the JSON Schema is consumed (which components, which composables, which validation hooks).
> - JSON Schema features the form generator relies on (or assumes), especially any extensions that LinkML's `gen-json-schema` does not currently emit (see [Open questions](../../OVERVIEW.md#open-questions--unknowns)).
> - The frontend's local dev story: how to launch backend + frontend, where to point them at an alternate JSON Schema for the parity check.
> - Vue 3 idioms used in `dandi-archive` (Composition API vs. Options API, state management, TypeScript usage, test framework).

## References

External skill/agent definitions to **lift content from** (review for fit before adopting wholesale — these are community collections of varying quality):

- [`anthropics/skills`](https://github.com/anthropics/skills) — canonical reference for the `SKILL.md` format and frontmatter conventions. The [`frontend-design`](https://github.com/anthropics/skills/tree/main/skills/frontend-design) and [`webapp-testing`](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) skills are the most directly relevant here.
- [`VoltAgent/awesome-claude-code-subagents` → `vue-expert.md`](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/02-language-specialists/vue-expert.md) — a Vue 3 Composition API + Pinia + Nuxt 3 specialist; a useful starter for "what knobs a Vue skill describes."
- [`rohitg00/awesome-claude-code-toolkit` → `vue-specialist.md`](https://github.com/rohitg00/awesome-claude-code-toolkit/blob/main/agents/language-experts/vue-specialist.md) — alternative phrasing of the same role.
- [`wshobson/agents`](https://github.com/wshobson/agents) — large, production-leaning marketplace (191 agents / 155 skills). Search for frontend / Vue entries.

`dandi-archive`-specific references:

- TODO: link the repo's frontend `README.md`, `CONTRIBUTING.md`, or `DEVELOPMENT.md` (whichever exist) once a session actually launches the frontend locally.
