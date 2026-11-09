# Patch queue (`tools/linkml_conversion`)

Inventory of the branches listed in the `branches_to_merge` array of [`tools/linkml_conversion`](../../../../tools/linkml_conversion). These branches are materially **part of the translation's input**: the script applies them, in order, on top of `linkml-conversion` before writing the regenerated artifacts to `linkml-auto-converted`. Order matters (per the script's comment).

A patch-queue entry is meant to be **temporary**. Each branch should be retired — by landing it on `master` or by removing its need (e.g. fixing the underlying issue upstream in `pydantic2linkml`) — once its exit criterion is met. This file is what lets us audit "can we drop any of these yet?" instead of treating the script's list as tribal knowledge.

## Entry template

```
### `<branch-name>`

- **Purpose:** what this branch changes and why it's applied during translation.
- **Rationale:** why the change isn't (or can't yet be) on `master` or fixed upstream.
- **Exit criterion:** the concrete condition under which this branch can be dropped from the queue.
- **Status:** active / blocked-on-X / ready-to-retire.
- **Ordering note:** why it sits where it sits in the list (if non-obvious).
```

---

## Current queue (in apply order)

### `master`

- **Purpose:** keep `linkml-conversion` up to date with `master` during each translation run, so the regenerated artifacts reflect the latest upstream Pydantic sources.
- **Rationale:** `linkml-conversion` is a long-lived branch that diverges from `master`; folding `master` in at translation time avoids carrying a manual rebase burden on `linkml-conversion` itself.
- **Exit criterion:** when `linkml-conversion` is itself merged to `master` (i.e. the migration's source-of-truth flip happens), this entry becomes unnecessary.
- **Status:** active. Expected to remain in the queue until the migration completes.
- **Ordering note:** applied first so subsequent patch branches stack on a current base.

### `remove-discriminated-unions`

- **Purpose:** remove the use of Pydantic discriminated unions from `dandischema/models.py` so the Pydantic sources fed to the translator don't contain a construct LinkML can't represent. The branch is a single commit on top of `master`, +6/−21 in `dandischema/models.py` only.
- **Rationale:** LinkML has no faithful equivalent to Pydantic v2 discriminated unions. Removing them on a separate branch lets the translation succeed without committing the removal to `master`, because the downstream impact on the **dandi-archive frontend** of dropping discriminated unions is not yet characterized.
- **Exit criterion:** **either** (a) the impact on dandi-archive is assessed and acceptable, at which point this branch lands on `master` and is dropped from the queue; **or** (b) `pydantic2linkml` gains a way to translate discriminated unions into a LinkML construct with equivalent validation behavior, at which point the removal is no longer needed and this branch is dropped without merging.
- **Status:** active, blocked on assessing the frontend impact (and/or on an upstream `pydantic2linkml` improvement). Track in `log.md` as that investigation progresses.
- **Ordering note:** applied after `master` so it patches the current Pydantic sources rather than a stale snapshot.

---

## When changing the queue

- Edit `tools/linkml_conversion`'s `branches_to_merge` array, and **update this file in the same change** — the script comment authorizes editing the list, but an undocumented edit makes the queue opaque again.
- A new entry without a written **exit criterion** is a smell: if there's no condition under which the branch can be retired, it's effectively a permanent patch and probably belongs on `master` (or upstream) — not in the queue.
- Removing an entry: note in `findings.md` what was learned that allowed retirement, so the rationale isn't lost.
