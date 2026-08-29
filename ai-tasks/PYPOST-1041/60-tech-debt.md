# PYPOST-1041: Technical Debt Analysis

## Overview

PYPOST-1041 hardened the DisplayRole ownership fitness function. The delivered diff is
**test-only**:

- `tests/test_display_role_scan_ownership.py` — modified, 55 insertions / 3 deletions
  (`_module_all_exports` helper plus the AC-1/AC-2/AC-3 assertions).
- `tests/test_display_role_scan_ownership_repro.py` — new, untracked (5 Step 3 repro tests).

No production module was touched: `pypost/agent/tree_index.py` already delegated to
`display_role_equals` and already declared a conforming `__all__`, so there is no runtime
behaviour, API, logging, or metric change to carry debt.

This step **carries forward** the findings already recorded in `50-observability.md`
(OBS-1..OBS-5) and `40-code-cleanup.md` rather than re-deriving them, adds three findings from a
fresh audit of the delivered guard, and records the pre-existing full-suite failures triaged at
Step 4. **Nothing found is a blocker.**

### Carried-forward map (de-duplication)

| Upstream finding | Recorded in | Step 7 disposition |
| --- | --- | --- |
| OBS-1 fail-fast single test function | `50-observability.md` | **TD-2** (Low-Medium, ticket candidate) |
| OBS-2 `missing X` diagnostics not self-describing | `50-observability.md` | **TD-6** (Low, ticket candidate) |
| OBS-3 no diagnostic prints a file path | `50-observability.md` | **TD-7** (cosmetic — recommend no ticket) |
| OBS-4 message wording pinned by repro regexes | `50-observability.md` | **TD-9** (informational — in-task Step 8 doc) |
| OBS-5 non-literal `__all__` reported as `found []` | `50-observability.md` | **TD-1** (Low-Medium, most actionable) |
| "Load-bearing repetition, deliberately not deduped" | `40-code-cleanup.md` | **TD-5** (Low, discoverability gap) |
| Step 6 re-review wording nit | this document | **TD-8** (cosmetic) |

New in this step, from an audit of the delivered guard: **TD-3** (mutation-matrix gap, proven) and
**TD-4** (substring heuristic admits a false green, proven).

---

## Shortcuts Taken

1. **`_module_all_exports` recognises only the plain literal `__all__` spelling.**
   The helper (`tests/test_display_role_scan_ownership.py:60-82`) matches `ast.Assign` only, which
   was the narrowest form that turned the Step 3 repro green against the real `tree_index.py`.
   The annotated spelling `__all__: list[str] = [...]` parses to `ast.AnnAssign` and is skipped.
   Cost recorded as **TD-1**.

2. **The whole contract stayed in one test function.**
   Fourteen assertions share `test_flat_and_tree_share_display_role_match_helper`, so a run reports
   the first violation only. This was not laziness: repro tests 4-5 call that function *by name*
   and assert a single `AssertionError`, so splitting it in Step 4 would have broken the reviewed
   red-then-green repro. Cost recorded as **TD-2**.

3. **The repro identifies its target by a substring heuristic.**
   `_refers_to_find_child` (`tests/test_display_role_scan_ownership_repro.py:126-134`) accepts any
   `ast.Name` whose id contains `"child"`, deliberately, so the guard survives either spelling of
   the local (`find_child` or the full symbol name). The leniency has a false-green edge, recorded
   as **TD-4**.

4. **No production edit** — by design, not a shortcut. `10-requirements.md` puts `ui_select`
   behaviour, errors, logging, and metrics under Non-Goals, and NFR-4 forbids runtime change.

---

## Code Quality Issues

### TD-1 — `_module_all_exports` misreads an annotated or computed `__all__` as empty

**Severity: Low-Medium.** Carried from OBS-5; the single most actionable item in this document.

- **File / symbol:** `tests/test_display_role_scan_ownership.py:60-82`, `_module_all_exports`,
  specifically the `isinstance(node, ast.Assign)` filter on line 68.
- **What is wrong:** an `ast.AnnAssign` is not an `ast.Assign`. Two spellings of a *correct*
  manifest therefore return the empty set and fail with
  `pypost.agent.tree_index.__all__ must export [...]; found []` — the annotated literal
  `__all__: list[str] = [...]` and a computed `__all__ = list(_PUBLIC)`. The message reads as
  "the manifest is empty" when the manifest is correct, so the CI reader is pointed at the wrong
  defect.
- **Reachability:** unreachable at this commit and one token from reachable. Re-verified during
  this step across `pypost/**/*.py`: **49** module-level `__all__` declarations, all plain literal
  `ast.Assign`; **0** `ast.AnnAssign`; **0** `ast.AugAssign`. Adding `: list[str]` to the existing
  literal in `tree_index.py` — a behaviour-preserving typing edit of exactly the kind the repo's
  `make typecheck` mypy baseline invites — turns the green ownership contract red and blames an
  empty manifest.
- **Proposed fix** (OBS-5 called it "widening one `isinstance`"; the smallest *correct* form is
  four lines, because `ast.AnnAssign` exposes `target` singular and may carry `value=None`):

  ```python
  for node in ast.iter_child_nodes(tree):
      if isinstance(node, ast.Assign):
          targets: list[ast.expr] = list(node.targets)
      elif isinstance(node, ast.AnnAssign):
          targets = [node.target]
      else:
          continue
      if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
          continue
      value = node.value          # None for a bare `__all__: list[str]`
      if isinstance(value, (ast.List, ast.Tuple)):
          ...                     # unchanged
  ```

- **Optional second half:** the diagnostic still cannot distinguish "no literal `__all__` found"
  from "literal `__all__` is empty". Returning `set() | None` (or emitting
  `no literal __all__ assignment found` for the `None` case) removes the remaining ambiguity for
  the computed form, which the `isinstance` widening alone does not fix.
- **Accepted, not fixed:** `__all__ += [...]` / `__all__.extend(...)` augmentation is still
  invisible to the helper. Zero occurrences under `pypost/` (verified above); documented rather
  than coded around.

### TD-2 — Fail-fast structure reports one violation per CI run

**Severity: Low-Medium.** Carried verbatim from OBS-1.

- **File / symbol:** `tests/test_display_role_scan_ownership.py:85-154`,
  `test_flat_and_tree_share_display_role_match_helper` — 14 assertions, AST-counted, in one
  function.
- **What is wrong:** a mutant that both inlines `DisplayRole` *and* empties `__all__` reports only
  the first message; the second breakage is invisible until the first is fixed and CI is re-run.
  A maintainer landing a broad refactor pays one CI round trip per violation.
- **Proposed fix:** accumulate instead of splitting the function — collect messages into a
  `violations: list[str]` and end with
  `assert not violations, "\n".join(violations)`. This keeps the single entry point that repro
  tests 4-5 call by name, keeps the suite's test count, and keeps every `pytest.raises(match=...)`
  regex working (each message stays on its own line, and `re.search` still finds it). The
  `find_child is not None` / `find_tree is not None` presence checks must stay short-circuiting,
  since the downstream probes would raise on `None`.
- **Why not done here:** Step 4's reviewed repro was written against the fail-fast shape; changing
  it now would re-open Steps 3-6.

### TD-3 — The repro cannot detect a single flat-finder assertion being disabled

**Severity: Medium.** New finding; proven by probe, not inferred.

- **Files / symbols:** `tests/test_display_role_scan_ownership_repro.py:100-108` (the two mutants)
  and `:218-238` (`test_repro_ownership_suite_catches_inlined_display_role_mutant`, whose regex is
  `r"find_child_index_by_display_text.*(display_role_equals|DisplayRole)"`).
- **What is wrong:** `_MUTANT_INLINE_DISPLAY_ROLE_CODE` violates AC-1 **and** AC-2 at once (it
  drops the `display_role_equals` call *and* inlines the comparison), and the test's regex accepts
  either assertion's message. So the mutant does not distinguish which of the two guards fired,
  and the source-shape tests 1-2 that are supposed to distinguish them can be satisfied by a call
  site that is never executed.
  Verified with an AST-level probe over in-memory variants (no repo file was modified):

  | Variant applied to the ownership suite | repro 1 | repro 2 | repro 3 | repro 4 | repro 5 |
  | --- | --- | --- | --- | --- | --- |
  | AC-1 delegation assert moved into an uncalled helper | pass | pass | pass | pass | pass |
  | AC-2 inline-prohibition assert moved into an uncalled helper | pass | pass | pass | pass | pass |
  | AC-4 `find_tree` assertion pair deleted outright | pass | pass | pass | pass | pass |

  In other words: either flat-finder guard can be silently retired, and the AC-4 assertions have no
  mutant at all, with the entire PYPOST-1041 repro suite still green.
- **Proposed fix** (one change, same file and template):
  1. Add a third mutant `_DELEGATING_AND_INLINING_FIND_CHILD` — calls `display_role_equals` *and*
     touches `Qt.ItemDataRole.DisplayRole` — with a test pinned to
     `match=r"must not compare ItemDataRole\.DisplayRole inline"`. The source already exists: it is
     row 2 of the diagnostics table in `50-observability.md`, driven ad hoc during Step 6 and never
     committed.
  2. Tighten the existing test 4 regex to `r"must call display_role_equals"` so it pins AC-1 alone.
  3. Parametrise `_MUTANT_TREE_INDEX_TEMPLATE` on the tree finder as well and add an
     inlined-`find_tree` mutant, so AC-4's "regression invariance" is enforced by a mutation rather
     than by the assertions merely existing.
- **Why it matters:** the ticket's whole premise is that a green suite is not evidence of an intact
  contract. That premise applies to the repro itself.

### TD-4 — `_refers_to_find_child` substring heuristic admits a false green

**Severity: Low.** New finding; proven by probe.

- **File / symbol:** `tests/test_display_role_scan_ownership_repro.py:126-134`,
  `_refers_to_find_child` — `if isinstance(arg, ast.Name) and "child" in arg.id.lower()`.
- **What is wrong:** the guard accepts *any* local whose name contains `"child"`. A refactor such
  as `for child_fn in (find_tree,): assert _calls_name(child_fn, "display_role_equals")` satisfies
  `_has_find_child_delegation_check` while `find_child_index_by_display_text` is never checked.
  Confirmed: the probe returned `True` for exactly that variant.
- **Proposed fix:** replace the substring test with an exact allowlist —
  `arg.id in {"find_child", "find_child_index_by_display_text"}` — keeping the existing
  `ast.dump(arg)` fallback for the lookup-expression spelling. This preserves the leniency
  `40-code-cleanup.md` intended (either spelling of the local) and removes the accidental-match
  surface.

### TD-5 — The load-bearing repetition constraint is not discoverable from the code

**Severity: Low** (near-zero cost to fix, high leverage).

- **Files / symbols:** `tests/test_display_role_scan_ownership.py:111-118`, `:133-140`, `:148-153`
  — the three repeated `_calls_name(...)` / `_has_display_role_attr(...)` assertion pairs.
- **What is wrong:** `40-code-cleanup.md` explains that folding these into a loop or a shared
  `_assert_delegates(...)` helper would rename the first argument to a generic `fn`, defeat
  `_refers_to_find_child`, and silently turn the mutation guard into a no-op. That explanation
  lives **only** in an `ai-tasks/` artifact. Nothing in the test file itself says so, and a
  maintainer running a "remove obvious duplication" pass — or a linting agent — has no way to
  learn it before deleting it. This is exactly the failure mode the ticket exists to prevent, one
  level up.
- **Proposed fix:** a three-line comment above the first assertion pair, naming the coupling:

  ```python
  # Do not fold these per-function assertion pairs into a loop or a shared helper:
  # tests/test_display_role_scan_ownership_repro.py::_refers_to_find_child matches the
  # *first argument* of _calls_name / _has_display_role_attr, so a generic `fn` parameter
  # silently turns the mutation guard into a no-op. The repetition is load-bearing.
  ```

- **Also:** Step 8 (`doc/dev/`, AC-6) should state the same constraint next to the AST boundary
  rules. That half is in-task and needs no ticket.

### TD-6 — Two pre-existing diagnostics are not self-describing

**Severity: Low.** Carried verbatim from OBS-2.

- **File / symbol:** `tests/test_display_role_scan_ownership.py:132` (`"missing
  find_tree_index_by_display_text"`) and `:143` (`"missing _select_item_view"`).
- **What is wrong:** neither names the owning module (`pypost/agent/tree_index.py`,
  `pypost/agent/ui_actions.py`) nor the remedy, unlike the
  `pypost.agent.tree_index must define ...` message a few lines above. A CI reader must open the
  test file to learn which production file to edit.
- **Proposed fix:** two message strings, mirroring the existing house wording — e.g.
  `"pypost.agent.tree_index must define find_tree_index_by_display_text (recursive DisplayRole
  scan)"` and `"pypost.agent.ui_actions must define _select_item_view (item view selection
  action)"`.
- **Why not done here:** AGENTS.md's out-of-scope-edit prohibition. This ticket's scope is the flat
  finder and the export manifest. (AC-4 is *not* the reason: it pins those assertions' intent, not
  their wording, and must not be cited as if it forbade the improvement.)

### TD-7 — No diagnostic prints a file path

**Severity: cosmetic. Recommend closing without a ticket.** Carried from OBS-3.

Of 14 assertions, 4 name the dotted module, 8 name only a function, 2 are the `is_file()` guards
that already interpolate `_TREE_INDEX` / `_UI_ACTIONS`. Cost to the reader is one
`grep -rn "def find_child_index_by_display_text"`. Recorded for completeness; not worth a ticket
on its own, and it would be free to fold into TD-6 if that one is picked up.

### TD-8 — `50-observability.md` Validation Results miscounts distinct messages

**Severity: cosmetic (documentation accuracy).** Found in the Step 6 re-review.

- **File:** `ai-tasks/PYPOST-1041/50-observability.md`, "Validation Results", the bullet reading
  "8 violation scenarios driven across 9 mutants ... and all **8 distinct messages** captured
  verbatim".
- **What is wrong:** rows 3 and 5 of the diagnostics table emit byte-identical text
  (`... must export [...]; found []` — the `__all__ = []` mutant and the non-literal `__all__`
  spellings). There are **8 scenarios and 7 distinct strings**; the identity of rows 3 and 5 is in
  fact the substance of OBS-5, so calling them distinct undercuts the finding it sits next to.
- **Proposed fix:** replace "all 8 distinct messages captured verbatim" with "all 8 scenarios
  captured verbatim (7 distinct strings — the `__all__ = []` and non-literal spellings are
  byte-identical, which is OBS-5)".
- **Recorded, not corrected:** `50-observability.md` is an accepted Step 6 artifact. Per
  `td-roadmap`, editing it would require re-opening STEP 6 to `[/]` and re-running its gate — a
  disproportionate churn for one clause. Whoever next re-opens that file should apply the wording
  above.

### TD-9 — Diagnostic wording is a machine-checked contract (informational)

Carried from OBS-4; **not debt, a constraint to document.** Repro tests 4-5 pin the message text
with `pytest.raises(match=...)`. A future reword must keep the function name and the helper name on
**one** line (`.` does not match a newline) and must keep `__all__` before `export`. In-task action:
Step 8 documents this next to the boundary rules. No ticket.

### Not debt (audited, deliberately left as-is)

- **The expected export names are hardcoded in four places** — `expected_exports` in the ownership
  suite, `required` in the repro, `_COMPLIANT_EXPORTS` in the mutant template, and
  `tree_index.__all__` itself. This is intended: a fitness function that derived its expectation
  from the source it audits would assert nothing. Not debt.
- **`_parse_file` in the repro duplicates `ownership_suite._parse`** — deliberate, per
  `40-code-cleanup.md`: the repro must detect a broken or deleted parser in the module it audits.
- **Architecture conformance** — no material deviation from `20-architecture.md`. The one
  difference is an improvement made in Step 5: `_module_all_exports` iterates
  `ast.iter_child_nodes(tree)` instead of the design sketch's `getattr(tree, "body", [])`.
  Every specified diagnostic message was implemented as written.

---

## Missing Tests

**Timeout markers — PASS, no BLOCKER.** Both modules declare `pytestmark = pytest.mark.timeout(10)`
after their imports, per `do-testing` and the PYPOST-1070 E402 rule:
`tests/test_display_role_scan_ownership.py:10` and
`tests/test_display_role_scan_ownership_repro.py:29`.

Coverage gaps, all tracked above rather than duplicated here:

- **Mutation matrix (TD-3)** — no mutant isolates AC-1 from AC-2, and AC-4's assertions have no
  mutant at all. This is the only genuine test gap in the diff.
- **`__all__` spellings (TD-1)** — no test drives an annotated or computed `__all__` through
  `_module_all_exports`; the case is only documented. The fix in TD-1 should ship with a unit test
  over the helper for the four spellings (literal list, literal tuple, annotated literal, absent).

Not gaps: runtime behaviour of `display_role_equals`, `find_child_index_by_display_text`, and
`find_tree_index_by_display_text` is covered by the pre-existing PYPOST-941/971 suites and was not
changed by this task. No Qt or GUI coverage is owed — the diff starts no `QApplication`.

---

## Performance Concerns

**None.** The suite parses two source files (`tree_index.py` 57 LOC, `ui_actions.py` ~450 LOC) with
`ast.parse` and runs pure predicates over the trees: no `QApplication`, no display server, no
network, no disk writes beyond two reads. Measured at Step 6: both modules together run in 1.18 s
wall clock including interpreter start-up and collection, with actual assertion work far inside
NFR-1's 200 ms. The accumulate-violations fix proposed in TD-2 adds a list append per violation and
changes nothing measurable.

---

## Follow-up Tasks

### New — proposed Debt issues (ticketed)

| ID | Priority | Summary | Component | Jira |
| --- | --- | --- | --- | --- |
| TD-3 | Medium | Extend the repro mutant matrix so AC-1, AC-2, and AC-4 are each pinned by their own mutant; tighten test 4's regex to `must call display_role_equals` | `tests/test_display_role_scan_ownership_repro.py` | [PYPOST-1236](https://pypost.atlassian.net/browse/PYPOST-1236) |
| TD-1 | Low-Medium | Teach `_module_all_exports` the `ast.AnnAssign` spelling (+ unit test over the four `__all__` forms) | `tests/test_display_role_scan_ownership.py` | [PYPOST-1235](https://pypost.atlassian.net/browse/PYPOST-1235) |
| TD-2 | Low-Medium | Accumulate ownership violations and report them in one `AssertionError` instead of failing on the first | `tests/test_display_role_scan_ownership.py` | [PYPOST-1237](https://pypost.atlassian.net/browse/PYPOST-1237) |
| TD-4 | Low | Replace the `"child" in arg.id.lower()` heuristic with an exact-name allowlist | `tests/test_display_role_scan_ownership_repro.py` | [PYPOST-1238](https://pypost.atlassian.net/browse/PYPOST-1238) |
| TD-5 | Low | Add the "repetition is load-bearing" comment above the assertion pairs | `tests/test_display_role_scan_ownership.py` | [PYPOST-1239](https://pypost.atlassian.net/browse/PYPOST-1239) |
| TD-6 | Low | Give `missing find_tree_index_by_display_text` / `missing _select_item_view` a module name and a remedy | `tests/test_display_role_scan_ownership.py` | [PYPOST-1240](https://pypost.atlassian.net/browse/PYPOST-1240) |

All six were filed in Jira on 2026-08-29 during PYPOST-1041 Phase D, each with a Fibonacci
estimate from a read-only estimation subagent. Each carries a concrete patch in the section above. TD-1, TD-4, TD-5, and TD-6 are
single-hunk edits; TD-2 and TD-3 are one function each.

### New — recorded, no ticket recommended

- **TD-7** (no file path in diagnostics) — cosmetic; fold into TD-6 if that is picked up.
- **TD-8** (`50-observability.md` "8 distinct messages") — cosmetic wording; apply when that
  artifact is next re-opened, since correcting it now would re-open an accepted step.
- **TD-9** (message wording is regex-pinned) — informational; belongs in Step 8 of *this* task,
  not in a new ticket.

### Pre-existing full-suite failures (Step 4 triage, base commit `253403db`)

All eight test failures, plus the `make typecheck` gate below, were reproduced on the base commit in a throwaway worktree **before** this task's diff
existed, none touches `pypost/agent/tree_index.py`, `pypost/agent/ui_actions.py`, or either
ownership suite, and **all are already filed — do not create new issues for them.**

| Verdict | Test | Cause | Jira |
| --- | --- | --- | --- |
| NON-BLOCKER — pre-existing | `tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules` | Harness doc table drifted from the marked modules | [PYPOST-1231](https://pypost.atlassian.net/browse/PYPOST-1231) |
| NON-BLOCKER — pre-existing | `tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import` | Encrypted export round-trip failure | [PYPOST-1232](https://pypost.atlassian.net/browse/PYPOST-1232) |
| NON-BLOCKER — pre-existing | `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir` | 642 E402 findings from `tests/test_examples_modernization*.py` and `tests/test_ui_library_manager.py` | [PYPOST-1233](https://pypost.atlassian.net/browse/PYPOST-1233) |
| NON-BLOCKER — pre-existing | `tests/test_makefile.py` | `WORKER_TIMEOUT=120` exceeded under parallel load | [PYPOST-1234](https://pypost.atlassian.net/browse/PYPOST-1234) |
| NON-BLOCKER — pre-existing | `tests/test_dialogs_audit.py::TestDialogsAuditInventory::test_audit_report_lists_every_dialog_module` | Dialog audit inventory / LOC aggregate baseline drift | [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (commented) |
| NON-BLOCKER — pre-existing | `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` | Same root cause as the row above | [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (commented) |
| NON-BLOCKER — pre-existing | `tests/test_environment_export_ui.py` | Qt-teardown crash in a shared pytest process | [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) (epic; children [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212) / [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) / [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214)) |
| NON-BLOCKER — pre-existing | `tests/test_main_window_alert_reload.py` | Qt-teardown crash in a shared pytest process | [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) (epic; same children) |
| NON-BLOCKER — pre-existing | `make typecheck` gate (not a pytest node) | mypy baseline 201 vs 243 errors at base commit `253403db`; verified in a throwaway worktree during Phase F | [PYPOST-1241](https://pypost.atlassian.net/browse/PYPOST-1241) |

---

## Blocker Review

| Check | Requirement | Status | Notes |
| --- | --- | --- | --- |
| **Pytest timeouts** | Explicit timeout marker on all tests (`do-testing`) | PASS | `pytestmark = pytest.mark.timeout(10)` in both modules |
| **Static analysis** | `make lint` clean | PASS | flake8 on `pypost/`, Markdown lint 16 files, link check 18 files — 0 findings |
| **Targeted tests** | Task suites green | PASS | Step 6: 2 files, 6/6 tests, 1.18 s (`make test PYTEST_ARGS=...`) |
| **Full suite** | Fast suite green | N/A this step | Not re-run: known Qt worker segfault + ~110 MB core dump. Step 4 iteration 3 holds the triage of the 8 pre-existing failures above |
| **Architecture alignment** | Matches `20-architecture.md` | PASS | No material deviation; one documented Step 5 improvement |
| **Diff integrity** | Test-only diff unchanged by Step 7 | PASS | `tests/test_display_role_scan_ownership.py` 1 file, 55 insertions / 3 deletions; repro file untracked; no code touched in this step |
| **Verdict** | Gate readiness | **PASS — no blockers** | 6 ticket candidates, 3 recorded-only, 8 pre-existing failures already filed |

### Verification of this step

- `make lint` — clean (0 findings).
- Evidence for TD-3 and TD-4 came from a throwaway AST probe under the session scratchpad that
  built modified copies of the suite **in memory**; no repository file was written, and
  `git diff --stat` still reports one file, 55 insertions / 3 deletions.
