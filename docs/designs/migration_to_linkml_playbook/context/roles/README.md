# Roles

A "role" is a profile of mindset, expertise, and operating habits that a working agent loads when handling a particular slice of this migration. Roles let an agent acquire the specialization a task needs by loading the relevant role files into its context. The same role files are also usable as spawn-prompt material when a subagent is invoked.

## How roles are used

- **Default mode — one agent, multiple roles loaded.** Migration work is deeply coupled: a frontend rendering question can implicate the JSON Schema, the LinkML schema, and the Pydantic source all at once (see [Success criteria](../../OVERVIEW.md#success-criteria), especially criterion 3). When a session touches more than one slice, the working agent loads the relevant role files into its context and stacks them — one mind, multiple specializations.
- **Subagent mode — when isolation is the actual benefit.** Subagents *may* be invoked for sub-tasks where isolation pays off: a noisy cross-repo search via `Explore`, an unbiased review of a migration PR, a verifiably-independent piece that can run in parallel for wall-clock speedup. When a subagent is invoked, **load the role(s) appropriate to its task into the spawn prompt** so it inherits the right specialization — subagents do *not* share the parent's loaded skills.

These two modes are not in conflict. The default mode handles coupled work (most of the migration); the subagent mode is a release valve for the cases listed in the analysis above.

## The senior-developer baseline

[`senior-developer.md`](senior-developer.md) is a **mandatory baseline** for every agent acting in this project — the parent agent *and* every subagent it spawns. It describes operating habits (meticulousness, verifying uncertainty, reading local docs first, etc.) rather than topical expertise. Other role files build on top of it; they do not replace it.

**Rule:** when spawning a subagent, its spawn prompt must include the contents of `senior-developer.md` (inlined, or fetched at the start of its task) so the subagent operates under the same baseline as the parent. A subagent that has not loaded the baseline is operating off-spec.

## Roles inventory

- [`senior-developer.md`](senior-developer.md) — mandatory baseline (operating habits, not topical expertise). Inherited by every agent.
- [`vue.md`](vue.md) — Vue / dandi-archive frontend.
- [`django.md`](django.md) — Django / dandi-archive backend.
- [`linkml.md`](linkml.md) — LinkML schema authoring + the Pydantic↔LinkML translation pipeline.

## Ecosystem references

The Claude Code skill/subagent ecosystem is large and uneven; treat external definitions as **starting material to lift selectively**, not gospel. As of authoring:

- [`anthropics/skills`](https://github.com/anthropics/skills) — Anthropic's official `SKILL.md` examples; the canonical reference for the format and frontmatter.
- [`wshobson/agents`](https://github.com/wshobson/agents) — large production-leaning marketplace (~190 agents / ~155 skills) with multi-harness packaging.
- [`VoltAgent/awesome-claude-code-subagents`](https://github.com/VoltAgent/awesome-claude-code-subagents) — community catalog of ~100 specialized subagents, indexed by category and language.
- [`rohitg00/awesome-claude-code-toolkit`](https://github.com/rohitg00/awesome-claude-code-toolkit) — broader toolkit including agents, skills, commands, hooks.
- [`travisvn/awesome-claude-skills`](https://github.com/travisvn/awesome-claude-skills) — curated awesome-list.

Quality varies across these. When borrowing, prefer lifting *specific habits or descriptions* over wholesale adoption — and credit the source in the role file's References section.

## Adding a new role

- One topical area per file. If you can't summarize the scope in one sentence, it's probably two roles.
- State explicitly what the role is **not** responsible for, so stacking multiple roles doesn't double-cover.
- Keep the expertise inventory tight — every loaded role takes context. Don't add a role just to populate the matrix.
- Role files are subject to the [self-updating rule](../../OVERVIEW.md#keeping-this-playbook-current): when something is learned about how this slice of the system actually behaves, update the role file in the same unit of work.
