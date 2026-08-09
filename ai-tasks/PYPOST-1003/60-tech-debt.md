# PYPOST-1003: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE. This was a surgical data-shape fix
(`dict[str, str]` → `list[tuple[str, str]]` for `renamed` on both import
planners). No blockers. Remaining notes are low-severity gaps or
pre-existing debt already tracked elsewhere (PYPOST-987 follow-ups).

## Shortcuts Taken

- **None that compromise correctness.** The fix matches the architecture and
  Jira description exactly: change the accumulator type, switch writes to
  `.append((name, new_name))`, iterate the list in the two formatters, update
  three existing assertions, and add one 3-duplicate regression test per
  module.
- **Did not introduce a shared `keep_both` closure in
  `environment_import.py`.** Collection import already factors keep-both
  through one nested closure; environment import still has two inline write
  sites. Architecture Q&A and PYPOST-987 debt explicitly left that asymmetry
  alone — unifying the two modules was out of scope for this reporting-only
  fix.
- **Did not introduce a shared `RenamedPair` / NamedTuple type.** Plain
  `tuple[str, str]` matches both modules' existing style and keeps the diff
  minimal. Shared typing across the sibling modules remains optional hygiene,
  not required for DoD.

## Code Quality Issues

- **No new quality issues introduced by this diff.** Field annotations,
  local accumulators, write sites, and formatter loops are consistent within
  each module. flake8 is clean on the production files; the only flake8 E402
  in `tests/test_environment_import.py` is pre-existing and outside changed
  lines (recorded in `40-code-cleanup.md`).
- **Sibling-module parallelism remains deliberate duplication.** Collection
  and environment import still implement the same rename-summary shape
  independently. That is pre-existing structure, not a regression from this
  task. Merging them is still out of scope (see PYPOST-987 exclusions and
  this task's requirements).

## Missing Tests

**No blocker.** Both touched test modules declare mandatory explicit timeouts
per `.cursor/lsr/do-testing.md`:

- `tests/test_collection_import.py` — module-scope `pytest.mark.timeout(30)`
- `tests/test_environment_import.py` — module-scope `pytest.mark.timeout(60)`

DoD regression coverage is present: each side has
`test_three_duplicate_names_report_two_renames_each` asserting ordered rename
pairs and `len(result.renamed) == 2`.

Remaining gaps (all low severity; none block close):

- **No explicit 4+ duplicate combinatorial case.** DoD states that 4
  duplicates should report "Renamed: 3". The accumulator is a plain append
  loop (N-independent); 3-duplicate coverage already exercises the former
  last-write-wins failure mode. A 4-entry variant would only add
  combinatorial confidence.
- **Formatter path not asserted for multi-rename listing.** Collection
  `TestFormatResult` still covers a single KEEP_BOTH rename plus parse
  errors. Environment import has **no** `format_import_result` unit test at
  all (pre-existing). Multi-rename listing is covered indirectly because
  formatters iterate the same `result.renamed` list the planner tests pin.
- **Environment side still lacks a dedicated 2-duplicate in-file test**
  analogous to collection's `test_second_duplicate_is_renamed_without_a_decision`.
  The new 3-duplicate test subsumes that behavior for the bug under fix;
  the gap is historical asymmetry, not a hole in this fix's DoD.

## Performance Concerns

None. Replacing a dict assignment with `list.append` is amortized O(1) and
does not change asymptotic cost of planning or formatting. Rename count is
bounded by the number of incoming entries; no new I/O or UI-thread work.

## Deviations from Initial Architecture

None. Delivered shape matches `20-architecture.md`:

- `CollectionImportPlanResult.renamed` / `ImportPlanResult.renamed` →
  `list[tuple[str, str]]`
- Write sites use `.append((name, new_name))`
- Formatters iterate `for original, new_name in result.renamed:` (no
  `.items()`)
- UI consumers (`len` / truthiness only) untouched
- No new modules, dependencies, or public function signature changes

## Hardcoded Values

None introduced. Rename display strings and summary templates are unchanged;
only the container that feeds them changed.

## Pre-existing Issues Encountered (not caused by this task)

- flake8 E402 in `tests/test_environment_import.py` (import order after
  `pytestmark`) — pre-existing, left untouched.
- Broader import follow-ups from PYPOST-987 (atomicity, off-UI-thread parse,
  mypy baseline keying, misc test gaps) remain out of scope and already have
  Jira tickets (PYPOST-1004–1007). This task **is** PYPOST-1003, the rename-
  summary follow-up from that list.

## Follow-up Tasks

No new Jira Debt tickets required to close this story. Optional hygiene only:

1. **(Optional, Low)** Add a formatter-level assertion that a 3-duplicate
   plan prints both `"original" -> "new"` lines and the correct Renamed
   count — especially for `format_import_result`, which currently has no
   dedicated unit test.
2. **(Optional, Lowest)** Add a 4-duplicate planner case on one side if
   future rename-summary changes want combinatorial pinning beyond the
   3-entry regression.

Do **not** re-ticket PYPOST-1004–1007 from this review; they already track
the adjacent debt called out as out of scope in `10-requirements.md`.

## User documentation

N/A for this step. No user-guide wording documented the incorrect undercount;
behavior change is summary accuracy only. Developer-facing notes belong in
Step 8 (`doc/dev/`) if still needed.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | None |
| Missing pytest timeout markers | **Pass** — both test modules have module-scope timeouts |
| Hardcoded values | None introduced |
| Deviations from architecture | None |
| Acceptance gaps vs DoD | Met — 3+ duplicate count/list fixed and regression-tested on both sides |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1003 Step 7.
