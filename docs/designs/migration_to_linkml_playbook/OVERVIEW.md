# Migration to LinkML — Playbook

> **Status:** in progress. Active development branches: `linkml-conversion` (+ its patch-queue branches), `linkml-auto-converted` (translation output).
> **Entry point.** Read this file first. It links out to everything else; load deeper files only as a step needs them.
> **This playbook is self-updating.** Anyone working on the migration — human or AI assistant — must keep it current as new facts surface. See [Keeping this playbook current](#keeping-this-playbook-current) for what to update and where.

## Problem

Migrate `dandischema` from its current Pydantic-defined schema (`dandischema/models.py`) to a **LinkML-defined** schema, so that LinkML becomes the single source of truth and Pydantic models / JSON Schemas are *generated from* it.

## Success criteria

The migration is done when **all three** hold:

1. **Behavioral parity with current Pydantic models.** Data instances accepted/rejected by today's `dandischema/models.py` are accepted/rejected the same way when validated against the LinkML schema.
2. **Generated Pydantic models are drop-in replacements** for the hand-written ones, usable by:
   - this repo (`dandischema`),
   - [`dandi/dandi-cli`](https://github.com/dandi/dandi-cli),
   - [`dandi/dandi-archive`](https://github.com/dandi/dandi-archive).
3. **Generated JSON Schema** matches what the `Dandiset` Pydantic model currently emits, well enough to:
   - validate data instances, and
   - drive the dandi-archive frontend (form generation / UI).

## How the translation is wired today

The conversion is orchestrated by the shell script **[`tools/linkml_conversion`](../../../tools/linkml_conversion)**, which delegates the actual translation work to Hatch scripts defined in `pyproject.toml`. Mental model:

- **Sources live on `linkml-conversion`** (and on the patch-queue branches it lists — currently `master` and `remove-discriminated-unions`). This is where you edit:
  - the Pydantic source: `dandischema/models.py`,
  - the LinkML-side inputs consumed by the translator: `dandischema/models_merge.yaml` (passed via `-M`: deep merge — dicts merge recursively, lists append, file wins only on scalars and type mismatches), `dandischema/models_overlay.yaml` (passed via `-O`: shallow merge — top-level keys only). See [`context/roles/linkml.md`](context/roles/linkml.md#-m-vs--o-semantics-verified-against-pydantic2linkmls-source--toolspy770809) for the full per-type breakdown.
  - the import stub: `dandischema/models_importstab.py` (installed as `models.py` on the output branch — see step 4 below).
- **`./tools/linkml_conversion` runs the translation** and writes the result to the **`linkml-auto-converted`** branch (checkout flips during the script; tree must be clean before running). Order of stages:
  1. Apply the **patch queue** of branches on top of `linkml-conversion` — see [`context/patch-queue.md`](context/patch-queue.md). Order in that list matters.
  2. **Pydantic → LinkML** via `hatch run linkml-auto-converted:2linkml`. Pipeline:
     ```
     pydantic2linkml -M models_merge.yaml -O models_overlay.yaml dandischema.models
       | sed (scrub memory-address/line-number noise for stable output)
       | tools/linkml_conversion_tools/sanitize-yaml
       > dandischema/models.yaml
     ```
     The translator is [`pydantic2linkml`](https://github.com/dandi/pydantic2linkml); it consumes `models_merge.yaml` (`-M`) and `models_overlay.yaml` (`-O`) directly. The `sed` filter and `sanitize-yaml` are stabilization/cleanup.
  3. **Rename dance:** `git mv dandischema/models.py dandischema/models_orig.py`, then `git mv dandischema/models_importstab.py dandischema/models.py`. On `linkml-auto-converted`, the file at `dandischema/models.py` is the import stub from [`dandischema/models_importstab.py`](../../../dandischema/models_importstab.py) on `linkml-conversion` — read it there for current content. It re-exports the generated models from `models_linkml` and currently also pulls a few constants forward from `models_orig.py`. The stub is an evolving file; how those remaining `models_orig` imports get resolved over time is itself part of the open work. The original Pydantic source is preserved on `linkml-auto-converted` as `models_orig.py`.
  4. **LinkML → downstream artifacts** via `./tools/linkml_conversion_fromlinkml`, which orchestrates three Hatch scripts in order:
      - `2pydantic` → runs LinkML's `gen-pydantic --black --template-dir tools/linkml_conversion_tools/pydantic_templates dandischema/models.yaml > dandischema/models_linkml.py`. The Pydantic Jinja templates under `tools/linkml_conversion_tools/pydantic_templates/` are the customization point for the generated Pydantic.
      - `2json` → for each target class in `{Dandiset, Asset, PublishedDandiset, PublishedAsset}`, runs `gen-json-schema -t <Class> dandischema/models.yaml` → `dandischema/models_linkml/<Class>.json`. Files are then lowercased/dashed (`PublishedDandiset.json` → `published-dandiset.json`).
      - `pydantic2json` → runs `python tools/pubschemata.py` → `dandischema/models_pydantic/*.json` (JSON Schemas derived from the **original** Pydantic models, kept as the parity baseline).
   5. `pre-commit run --all` (best effort), then a commit.
- **Outputs on `linkml-auto-converted`** (all produced by the pipeline above — do not hand-edit):
  - `dandischema/models.yaml` — LinkML schema
  - `dandischema/models.py` — the installed import stub
  - `dandischema/models_orig.py` — original Pydantic source, preserved for reference and for the constants the stub still imports from it
  - `dandischema/models_linkml.py` — generated Pydantic
  - `dandischema/models_linkml/*.json` — JSON Schemas derived **from the LinkML schema** (one per target class, lowercased/dashed filenames)
  - `dandischema/models_pydantic/*.json` — JSON Schemas derived **from the original Pydantic models** (parity baseline, generated via `tools/pubschemata.py`)
- **`tools/linkml_conversion_tools/`** is a general drawer for any tool convenient to the LinkML migration. It is **not** structurally divided into "pipeline" vs "auxiliary" — files just live here, and some of them happen to be wired into the current pipeline. New migration-related tools belong here; whether they end up wired into the pipeline is a separate decision. As of now:
  - `sanitize-yaml` → wired in as the final pipe stage of `2linkml`. Internally a sub-pipeline that runs three Python helpers in order, each as a stdin→stdout filter:
    1. `remove_notes_by_pattern.py` — strips `notes:` entries matching a configured regex set.
    2. `remove_slot_usage_schemakey.py` — strips `schemaKey` entries inside `slot_usage` blocks.
    3. `sort_license_type_permissible_values.py` — sorts `enums.LicenseType.permissible_values` alphabetically for stable output.

    All three are run inside the `linkml-auto-converted` Hatch env. To add a new sanitization step, append another pipe to `sanitize-yaml` — that's its documented extension point ("Add further sanitization steps here as additional pipes").
  - `pydantic_templates/` → wired in; consumed by `gen-pydantic --template-dir` in `2pydantic`.
  - `find_schemakey_mismatches.py` → not currently called from anywhere; an on-demand tool that prints Pydantic models where the `schemaKey` default ≠ class name. Available to run by hand when a schemaKey question comes up.

  Verify a tool's current wiring from source before assuming — pipeline membership can change without renaming.
- **LinkML-behavior test envs** (separate from `tox`): `tests/linkml_behavior/` runs under its own Hatch envs:
  - `hatch run linkml-behavior-test:test` — runs the behavior tests under `pytest`.
  - `hatch run linkml-behavior-typing:check` — runs `mypy` against the tests.

  Both envs are **detached** (don't install `dandischema`); they exist because these tests probe LinkML itself, not our package.
- **LinkML-semantics tests:** `tests/linkml_behavior/` (e.g. `tests/linkml_behavior/required_refinement/`) is **not** a parity harness for our migration. Each subdirectory pins a specific *LinkML upstream behavior* that the generated dandischema LinkML relies on — e.g. `required_refinement/` exercises `required: False -> True` via `slot_usage` to defend against the issue tracked in [#405](https://github.com/dandi/dandi-schema/issues/405). Extend these only when a new LinkML semantic our schema depends on needs a contract test; parity testing of our migration belongs elsewhere (see [Approach](#approach--repeatable-procedure)).

## Upstream tool we own

[`dandi/pydantic2linkml`](https://github.com/dandi/pydantic2linkml) — the package doing most of the Pydantic→LinkML translation. Because **we own it**, systematic translation bugs should usually be fixed *there*, not patched downstream in this repo's overlays. See [Suggestions → "Push fixes upstream when possible"](#suggestions-open-leads).

## Approach — repeatable procedure

The procedure that's known to work. Follow in order; deviations belong in `log.md`.

1. **Make changes on `linkml-conversion`** (or the relevant patch-queue branch). Commit. Tree must be clean before step 2.
2. **Run `./tools/linkml_conversion`** from the repo root. It checks out `linkml-auto-converted` and writes the regenerated artifacts there.
3. **Inspect the diff on `linkml-auto-converted`** — both `models.yaml` and the generated `models_linkml.py` / JSON Schema files. Anything unexpected is a finding.
4. **Run the test/contract suites.** These check different things — don't conflate them:
   - **Full dandischema test suite:** `tox -e py3`.
   - **Lint + types:** `tox -e lint,typing`.
   - **LinkML-semantics contract tests** under `tests/linkml_behavior/` (`hatch run linkml-behavior-test:test`; type-check with `hatch run linkml-behavior-typing:check`) — these defend the *LinkML upstream behaviors* our schema relies on, not Pydantic↔LinkML parity.
5. **Run a parity check.** The migration's real success criterion (criterion 3) is that the LinkML-derived JSON Schema can drive `dandi-archive`'s frontend the same way the Pydantic-derived one does. Two complementary checks:
   - **Cheap structural diff:** compare the two JSON Schema sets produced on `linkml-auto-converted`: LinkML-derived (`dandischema/models_linkml/*.json`, via `gen-json-schema`) vs. Pydantic-derived baseline (`dandischema/models_pydantic/*.json`, via `tools/pubschemata.py`). Anything beyond expected, explained differences is a finding.
   - **End-to-end behavioral check (preferred when feasible):** drive the dandi-archive UI through representative flows with **Playwright MCP** and compare LinkML-derived behavior to the Pydantic-derived baseline. Two variants:
     - **Local stack:** launch the dandi-archive backend + frontend locally, point them at the LinkML-derived JSON Schema. Gives full control (you can swap schemas, set breakpoints, edit on the fly). Requires local clones of `dandi-archive`, `dandi-cli`, `dandischema`, and `pydantic2linkml`.
     - **Live production instance:** compare against the deployed frontend at <https://dandiarchive.org/>. Faster to reach for and known-good as a baseline, but you can only *observe* — you can't swap in the LinkML-derived schema there. Useful for snapshotting "what the Pydantic-derived schema actually drives the UI to do" and as a sanity reference; not a place to *test* the LinkML side.
6. **Diagnose any divergence** — between Pydantic-validated and LinkML-validated outcomes on the same instance, between the two JSON Schemas, or in the dandi-archive frontend behavior. Record in `log.md`; promote stable conclusions into `findings.md`.
7. **Decide where to fix:**
   - **In `pydantic2linkml`** if the issue is a systematic translation gap (whole class of types/constraints mishandled).
   - **In `dandischema/models_merge.yaml`** (consumed by `pydantic2linkml -M`) — deep merge: dicts merge recursively, lists append, file wins only on scalars and type mismatches. Use to override a scalar nested inside generated structure, or to *add* items to a list (e.g. extra `permissible_values`, extra slots). Cannot replace or reorder list items.
   - **In `dandischema/models_overlay.yaml`** (consumed by `pydantic2linkml -O`) — shallow merge of top-level keys. Use to add/replace whole top-level elements (classes, enums, prefixes), or to outright replace a top-level list that `-M` would have appended to.

   See [`context/roles/linkml.md`](context/roles/linkml.md#-m-vs--o-semantics-verified-against-pydantic2linkmls-source--toolspy770809) for the full decision matrix.
   - **In `dandischema/models.py`** if the Pydantic source itself is the right place (e.g. an under-specified field).
   - Default preference: upstream first.
8. **Pin the fix with a test** at the layer that caught it — no fix lands without a test that would have caught it:
   - A failure that came from a LinkML semantic our schema relies on → add a contract test under `tests/linkml_behavior/`.
   - A failure caught by the structural JSON Schema diff → add the comparison (or a stable subset of it) as a checked-in fixture/test.
   - A failure caught only end-to-end in dandi-archive → at minimum, record the reproduction in `log.md` and link it from `findings.md`; consider whether it can be reduced to a unit/contract test at one of the earlier layers.

## Suggestions (open leads)

Speculative — graduate into the procedure above once confirmed, or kill into `findings.md` with reasoning.

- **Push fixes upstream when possible.** If a class of LinkML output is wrong for many Pydantic constructs, fix `pydantic2linkml` rather than carrying growing local overrides (`models_overlay.yaml` for corrections, `models_merge.yaml` for merges) here.
- **Use the `dandi-linkml-validation-report` skill** (already present on the LinkML branches under `.claude/skills/`) as a fitness signal — running the LinkML schema against real archive metadata exposes failure modes that synthetic tests miss.
- **Re-examine the patch queue** ([`context/patch-queue.md`](context/patch-queue.md)) when behavior drifts unexpectedly — order matters, and a stale branch in the list can silently revert hunks. Use that inventory to check whether any entry has met its exit criterion and can be retired.
- **Watch out for** Pydantic v2 features that LinkML can't express natively (custom validators, discriminated unions, `Annotated` metadata). These are the most likely sources of overlay accretion.

## Out of scope (for now)

- Renaming or restructuring classes purely for LinkML aesthetics — preserve current public class/field names to keep downstream consumers stable.
- Migrating `dandi-cli` / `dandi-archive` consumers off the generated models before parity is proven here.

## Keeping this playbook current

**The playbook is a living document, not a snapshot.** Whenever working on this migration — investigating, fixing, reading code, discovering tools, hitting a wall — keep this directory in sync with what is actually true. Stale instructions are worse than missing ones, because they get followed.

The triggers below are **illustrative, not exhaustive** — they're common shapes the update need takes, not the full set. Anything that would make this playbook a more accurate or more useful guide for the next attempt qualifies, even if it doesn't fit any bullet here. When in doubt, write it down.

- **New fact discovered** about how the translation, the schema, the consumers, or the upstream tooling behaves → add to `log.md`; if it's stable and trustworthy, promote into `findings.md` and adjust any affected procedure step in this file.
- **Existing claim contradicted** by what you see in the code, the artifacts, or a test run → correct the claim in place (don't just append a footnote elsewhere) and note the correction in `log.md` so the history of *why it changed* is preserved.
- **New tool, script, command, or technique** found useful (whether in this repo, in `pydantic2linkml`, in LinkML's CLI, or anywhere else) → mention it where it would actually be reached for (procedure step, suggestion list, or as its own helper under `tools/`).
- **Procedure step turns out to be wrong, incomplete, or in the wrong order** → edit the [Approach](#approach--repeatable-procedure) section directly. The procedure is the part future attempts execute most literally; outdated steps cost the most.
- **Patch-queue branch changes** (added, removed, retired, exit criterion met) → update [`context/patch-queue.md`](context/patch-queue.md) in the **same** change as the edit to `tools/linkml_conversion`.
- **An open question gets answered** → remove it from the [Open questions](#open-questions--unknowns) list and fold the answer into the relevant section (or into `findings.md`).
- **A suggestion is confirmed or killed** → move it out of [Suggestions](#suggestions-open-leads) into the procedure (if confirmed) or into `findings.md` with the reasoning that retired it (if killed).
- **The success criteria, scope, or wiring change** → update the top of this file. These shape every downstream decision.

What this looks like in practice during a working session: when something is learned, the playbook edit is part of the same unit of work as the code change or the investigation, not a separate "cleanup" pass deferred to later (which never happens). A commit that lands a fix without touching the playbook, when the playbook had something wrong or missing about that area, is incomplete.

For an AI assistant working in this directory: treat playbook updates as a default expectation of the task, not an optional extra. If a session surfaces a fact that would have saved time at the start, that fact belongs in `findings.md` (or wherever it fits) before the session ends.

## How to use this directory

- **`log.md`** — append-only, dated. Raw attempts, observations, dead ends, partial wins. Don't over-curate.
- **`findings.md`** — distilled, durable conclusions promoted out of `log.md`. The thing a future attempt reads first.
- **`tools/`** — scripts/probes accumulated across attempts (diff helpers, ad-hoc validators, comparators). Each script should have a one-line header comment naming its purpose.
- **`context/`** — background material that doesn't belong in the procedure: design notes, references, deeper explanations of constraints, links to related discussions.
- **`context/roles/`** — role profiles a working agent loads when handling a slice of the migration. [`senior-developer.md`](context/roles/senior-developer.md) is a **mandatory baseline** every agent (parent or subagent) inherits; topical roles ([`vue.md`](context/roles/vue.md), [`django.md`](context/roles/django.md), [`linkml.md`](context/roles/linkml.md)) stack on top of it. See [`context/roles/README.md`](context/roles/README.md) for how this preserves coupled reasoning while still permitting subagents when isolation is genuinely beneficial.

When working in a fresh conversation, open this `OVERVIEW.md` first, then pull only the files the current step needs.

## Open questions / unknowns

- Which behavior gaps (if any) are *intentional* (deliberate cleanup during migration) vs. unintentional regressions from the Pydantic baseline.
- Whether `dandi-archive`'s frontend relies on JSON Schema *extensions* (`$comment`, custom keywords) that LinkML's `gen-json-schema` doesn't currently emit. (Partly answered for the *dialect* axis: LinkML emits draft 2019-09, Pydantic and the frontend's Ajv are on 2020-12, but the frontend deletes `$schema` so the gap is mostly cosmetic except for tuple arrays — see `findings.md`. The `$comment`/custom-keyword question is still open.)
- **Frontend impact of removing discriminated unions** — the active blocker on retiring the `remove-discriminated-unions` patch-queue branch (see [`context/patch-queue.md`](context/patch-queue.md)).
