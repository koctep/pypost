# PYPOST-942: List/tree out-of-range and missing-option tests

## Goals

Agent and golden-flow authors rely on `ui_select` for list and tree controls
introduced in [PYPOST-916](https://pypost.atlassian.net/browse/PYPOST-916).
When they pass a label that does not exist or an index outside the control,
they need the same clear, actionable failure they already get for combo
boxes — not silent mis-selection or ambiguous errors.

This debt closes [PYPOST-916/60-tech-debt.md](../PYPOST-916/60-tech-debt.md)
TD-4: happy-path list/tree select is covered, but dedicated negative-path
tests are missing.

## Programming Language

Python (PySide6), with English Markdown developer docs.

## User Stories

- As an **agent / e2e author**, I want a missing list or tree label to fail
  with an explicit “option not found” style error so I can fix drive scripts
  quickly.
- As an **agent / e2e author**, I want an out-of-range list or tree index to
  fail with an explicit out-of-range error so bad indices do not slip through
  CI.
- As a **maintainer**, I want list and tree negative select paths locked by
  automated tests mirroring combo missing-option coverage so regressions are
  caught before release.
- As a **CI owner**, I want negative select cases in the existing fixture
  suite with explicit pytest timeouts so the error contract stays green in
  every run.

## Definition of Done

- Automated tests assert clear errors when a list select target has no
  matching display text.
- Automated tests assert clear errors when a list select index is negative
  or beyond the last row.
- Automated tests assert clear errors when a tree select target has no
  matching display text.
- Automated tests assert clear errors when a tree select index is negative
  or beyond the last top-level row.
- Existing happy-path list, tree, and combo select tests remain passing.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`.

## Task Description

**Problem:** PYPOST-916 added list and tree select by display text and index.
Fixture tests prove successful selection, and combo boxes already have a
dedicated missing-option test. List and tree lack matching dedicated tests
for missing labels and out-of-range indices, so error behaviour could regress
without CI signal.

**Business need:** Consistent, test-backed failure messages across select
control types so harness authors trust the agent API and failures are
diagnosable in CI logs.

### In Scope

- Add dedicated automated negative-path tests for list select (missing text,
  out-of-range index).
- Add dedicated automated negative-path tests for tree select (missing text,
  out-of-range index).
- Align assertions with the existing combo missing-option error pattern
  (`UiTargetNotInteractableError` with actionable message text).
- Keep tests in the established offscreen Qt fixture style with explicit
  timeouts.

### Out of Scope

- Changing production UI widgets or the widget identity catalog.
- Altering select behaviour or error message wording (unless a test reveals a
  bug — then fix belongs in Step 4).
- Combo out-of-range index tests (combo missing-option test exists; index
  negative path is a separate gap).
- Model-backed `QListView` negative paths (PYPOST-939 scope; flat list view
  happy path only today).
- Live `COLLECTION_TREE` agent_e2e session proofs.
- Jira ticket creation, commit, or status transitions (orchestrator).

## Functional Requirements

- FR1: A list select with unknown display text raises an actionable agent UI
  error indicating the option was not found.
- FR2: A list select with index `< 0` or `>= row count` raises an actionable
  agent UI error indicating the index is out of range.
- FR3: A tree select with unknown display text raises an actionable agent UI
  error indicating the option was not found.
- FR4: A tree select with top-level index `< 0` or `>= top-level row count`
  raises an actionable agent UI error indicating the index is out of range.
- FR5: Each negative case above has at least one dedicated automated test.
- FR6: Existing combo, list, and tree happy-path select tests stay green.

## Non-Functional Requirements

- NFR1: Fixture-style offscreen Qt tests; no live network.
- NFR2: Explicit pytest timeouts per `.cursor/lsr/do-testing.md`.
- NFR3: Tests live alongside existing `ui_select` fixture coverage (primary
  module: `tests/test_ui_actions.py`).
- NFR4: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Parent debt: PYPOST-916 TD-4 (Low priority, non-blocker for PYPOST-916
  close).
- Select error implementation already exists for list/tree; this task adds
  test coverage, not new product behaviour.
- Tree index select applies to top-level rows only (PYPOST-916 contract);
  nested rows are selected by display text.
- Sprint-task-runner batch: no user approval gates; no commit / Jira writes
  in this subagent run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Agent / harness | Drives named UI after ready |
| Select action | Chooses one row on a named control |
| List control | Flat item list (`QListWidget` fixture) |
| Tree control | Hierarchical rows (`QTreeView` fixture) |
| Display text | Visible label used to find the item |
| Index | Zero-based position (list: any row; tree: top-level only) |
| Actionable error | Clear failure the author can fix in the drive script |

## Q&A

| Q | A |
| --- | --- |
| Why tests only — no code change? | List/tree error paths are implemented; TD-4 tracks missing dedicated tests. |
| Why mirror combo coverage? | Combo has `test_select_missing_option_raises`; list/tree need parity so CI catches drift. |
| Tree missing text already tested in `test_tree_index_walk.py`? | Partial overlap exists; this task adds dedicated fixture-suite tests per TD-4 acceptance. |
| Include `QListView` errors? | Out of scope — TD-4 names list/tree from PYPOST-916; QListView is PYPOST-939. |
| Must error strings match combo exactly? | Same error class and message pattern (`option not found` / `option index out of range`); exact wording follows existing implementation. |
| Jira / commit in this run? | No — parent orchestrator owns Phase D/F. |
