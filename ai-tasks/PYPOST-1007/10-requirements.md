# PYPOST-1007: Make mypy baseline gate resilient to line-number churn

## Programming Language

Python (existing gate script, no new language/stack).

## Goals

The mypy baseline gate (`scripts/check_mypy_baseline.py`, run via `make
typecheck`) exists to let the team carry a known set of pre-existing type
errors without blocking on them, while still failing the build the moment a
*new* error is introduced or catching pre-existing errors that get worse.

Today the gate identifies a baselined error by its file, line number, and
error code. A line number is incidental — it shifts whenever code above an
error moves, most commonly when an unrelated commit adds, removes, or
reorders an `import` statement in a heavily-baselined file. When that
happens, every baselined error below the shift is reported as both a "fixed"
error (the old line number disappears) and a "new" error (the same error
reappears at a new line number), even though nothing about the error itself
changed.

This produces two business-facing harms:

1. **Real regressions get lost in noise.** In PYPOST-987, an import change
   in `pypost/ui/collection_item_dialogs.py` shifted line numbers in the
   unrelated `pypost/ui/presenters/tabs_presenter_worker.py`, producing
   roughly 30 phantom "new error" entries. Buried in that list was one
   genuine new type regression. A developer (or reviewer) scanning that
   output has no efficient way to tell the one real problem from the 30
   false alarms, so the gate stops doing the one thing it exists for: making
   real regressions visible.
2. **The gate loses developer trust and gets worked around.** When a
   line-shift produces a wall of unrelated-looking "new errors," the
   instinctive reaction is to treat the gate as unreliable — either by
   re-running `--update-baseline` reflexively (which can silently absorb a
   real new error along with the noise) or by treating `make typecheck`
   as an "optional, ignore it" step, which is exactly the failure mode a
   baseline gate is supposed to prevent.

The business goal of this task is: **a developer touching a heavily-baselined
file for an unrelated reason (e.g. reordering imports) should see zero
phantom diff in the mypy gate**, so that when the gate does report a "new"
or "fixed" error, that report can be trusted to reflect an actual change in
the code's type-correctness — never mere line movement.

## User Stories

- As a developer running `make typecheck` (or the mypy baseline gate in CI)
  after touching imports or otherwise shifting code in a file that already
  has baselined mypy errors, I want the gate to report no changes, so that I
  am not forced to investigate a wall of false positives before I can trust
  the result.
- As a developer who introduces a genuine new mypy error, I want the gate to
  still flag it as new, so that regressions are always caught regardless of
  what else changed in the file.
- As a developer who fixes a pre-existing baselined error, I want the gate
  to still recognize it as resolved (so the baseline can be shrunk), so that
  cleanup work is properly credited and the baseline doesn't silently grow
  stale entries.
- As a reviewer reading gate output in a PR, I want the list of "new" and
  "fixed" errors to correspond only to errors that actually appeared or
  disappeared, so that I can evaluate a diff's type-safety impact without
  manually cross-referencing line numbers against the diff.
- As a maintainer of the mypy baseline gate, I want the existing safety
  guarantees (unknown/new errors block the gate, resolved errors are
  reported so the baseline can be tightened, the gate still works when the
  baseline file is missing) to keep working exactly as before, so that
  resilience to line-number churn is a strict improvement and not a
  weakening of the gate.

## Definition of Done

- A change that only moves line numbers within a file that already has
  baselined errors (e.g. adding/removing/reordering an import, adding a
  blank line, moving a function) produces **zero** new/fixed entries in the
  gate's output, provided none of the underlying errors actually changed.
- A mypy error that does not correspond to any pre-existing baselined error
  under whatever identity scheme Step 2 defines is still reported as "new"
  and still causes the gate to fail, exactly as it does today.
- A baselined error that is genuinely fixed (no longer produced by mypy,
  regardless of where in the file it used to be) is still reported as
  "fixed"/"resolved," exactly as it does today.
- Existing gate behaviors are preserved: the gate fails with a clear message
  when `mypy-baseline.json` is missing; `--update-baseline` still
  regenerates the baseline from the current mypy run; the reported error
  count still matches the number of baseline entries.
- Existing and updated automated tests in `tests/test_mypy_baseline.py`
  (and any new tests added for this task) pass, demonstrating both that
  line-shift noise is eliminated and that real new/fixed errors are still
  detected.
- No developer-facing workflow changes: the same `make typecheck` command
  and `--update-baseline` flag continue to work the same way from a user's
  perspective; only the false-positive/false-negative behavior around line
  numbers changes.

## Task Description

`scripts/check_mypy_baseline.py` runs mypy over `pypost/core`,
`pypost/models`, and `pypost/ui`, and compares the resulting errors against
a frozen baseline stored in `mypy-baseline.json`
(`{"scope": [...], "error_count": N, "errors": [...]}`). Each error is
currently identified using its source line number as part of its identity,
which is not a stable identifier — line numbers shift for reasons that have
nothing to do with the error itself (e.g. an import added above it).

This task is to change what makes a baselined error "the same error" so
that it survives incidental line-number movement, while still reliably
detecting errors that are genuinely new or genuinely fixed. This is a
tooling/CI-gate change internal to the development workflow; it has no
end-user-facing (application) behavior and does not touch `pypost/`
production code — only the gate script, its baseline data file, and its
tests are in scope.

Explicitly out of scope for this task (per PYPOST-987 follow-up #5, which
this task implements):
- Any change to application behavior or UI.
- Broadening or narrowing the set of directories mypy checks
  (`pypost/core`, `pypost/models`, `pypost/ui`).
- Resolving any of the mypy errors currently in the baseline.
- The specific new identity format for a baseline entry, how the baseline
  file's on-disk shape changes, or how backward compatibility with the
  current `mypy-baseline.json` is handled — those are architecture/
  implementation decisions for Step 2.

## Main Entities and Interactions

| Entity | Attributes | Role |
| --- | --- | --- |
| Gate script | Scope directories checked; pass/fail outcome | Runs mypy, compares its output to the baseline, and reports new/fixed errors |
| Baseline file | Scope; error count; recorded errors | Frozen record of previously-accepted errors the gate compares against |
| Baselined error | Identifying details; still present in current mypy run | A known, pre-existing error the gate should keep tolerating |
| New error | Identifying details; not present in baseline | An error the gate must flag and fail on |
| Fixed error | Identifying details; no longer produced by mypy | A previously-baselined error that has been resolved |
| Developer | Code changes; intent (unrelated churn vs. real fix) | Runs `make typecheck` locally, expects only real changes to surface |
| Reviewer | PR under review | Reads gate output on a PR to judge type-safety impact of a diff |
| CI | Gate invocation; build pass/fail | Runs the gate automatically and blocks on genuinely new errors |

Interaction overview:

1. A developer changes code (which may or may not touch type-checked
   files) and runs `make typecheck`, or CI runs the gate automatically.
2. The gate script runs mypy over the in-scope directories and gets the
   current set of errors.
3. The gate script compares the current errors against the baseline file:
   errors present in both are baselined (tolerated); errors only in the
   current run are new; errors only in the baseline are fixed.
4. If the change only moved code around (e.g. reordered imports) without
   altering any error, the comparison must find no new or fixed errors —
   the developer sees a clean result.
5. If the developer introduced a genuine new error, the gate reports it as
   new and fails, so both the developer and a reviewer see it called out.
6. If the developer resolved a baselined error, the gate reports it as
   fixed, so the baseline can later be tightened via `--update-baseline`.
7. A reviewer reads the gate's new/fixed report on a PR to evaluate the
   diff's type-safety impact without manually cross-referencing line
   numbers.

## Q&A

**Q: Why does line-number churn matter enough to fix — isn't "phantom new
errors" just cosmetic noise?**
A: No — it directly hides real regressions, as demonstrated in PYPOST-987
where a real new error in `tabs_presenter_worker.py` was buried among ~30
false positives caused by an unrelated import change elsewhere in the same
file. A gate that can't be trusted to surface real regressions defeats its
own purpose. See `ai-tasks/PYPOST-987/60-tech-debt.md`, Follow-up Task #5,
and the source discussion at `ai-tasks/PYPOST-987/60-tech-debt.md #5`.

**Q: Should the fix weaken the gate (e.g. by ignoring errors it can't
confidently match) to get rid of noise?**
A: No — the Definition of Done requires both directions to keep working:
genuinely new errors must still block, and genuinely fixed errors must still
be recognized as fixed. Eliminating noise and preserving detection power are
both mandatory; this is a strict improvement, not a trade-off.

**Q: Does this task change any application-facing behavior?**
A: No. This is purely a developer-tooling/CI-gate change. End users of the
pypost application are unaffected; only developers running `make typecheck`
or CI see any difference, and that difference is: fewer false positives,
same true positives.

**Q: What is out of scope regarding *how* errors are matched (e.g. exact
key fields, message normalization, baseline file format)?**
A: Per the rules in `.cursor/rules/10-requirements.mdc`, this requirements
document intentionally excludes implementation/architecture decisions. The
Jira description's suggestion of keying on `(file, error-code, message)` is
the originating idea and a candidate, but the concrete design (including
whether/how message text is normalized, how the baseline file's shape
changes, and migration of the existing `mypy-baseline.json`) is Step 2's
responsibility.

**Q: Is `make typecheck` a blocking gate today?**
A: Per `ai-tasks/PYPOST-987/60-tech-debt.md`, `make check` is `lint test
verify-ai-tasks`; `typecheck` is noted there as "an explicitly optional
gate." This task does not change that gate's role in `make check`/CI — it
only makes the gate's own output trustworthy when it does run.
