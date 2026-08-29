# PYPOST-1042: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: dedicated contract test `test_select_tree_no_model_raises` locks
`UiTargetNotInteractableError` with `"tree has no model"` for a model-less `QTreeView`
parametrized over both text and index selection requests (`["Alpha", 0]`); verified that
`"item view has no model"` is absent; companion mutation-evidence suite
`tests/test_ui_actions_tree_no_model_mutation.py` guarantees sensitivity against guard removal and
reason rewording. Module green; closes [PYPOST-972/60-tech-debt.md](../PYPOST-972/60-tech-debt.md)
TD-1. Zero production code changed.

## Shortcuts Taken

- **Mutation-evidence repro suite instead of classic red-before-green** — The production error path
  already existed in `_select_tree` (`pypost/agent/ui_actions.py:243-246`), so the contract test
  was green on first run. To satisfy the TDD requirement and prove the contract test is not vacuous,
  `tests/test_ui_actions_tree_no_model_mutation.py` was created to verify red failure modes against
  mutated `_select_tree` definitions.
- **Substring assertions** — Asserts `"tree has no model"` in `str(exc_info.value)` and asserts that
  `"item view has no model"` is absent (AC-2, AC-3), mirroring `test_select_list_view_no_model_raises`
  style.
- **Inline isolated fixture** — Model-less `QTreeView` constructed directly in test setup rather
  than reusing `tests/helpers/collections_tree.py` (which always attaches a model and wires presenters).

## Code Quality Issues

None material.
- The new test `test_select_tree_no_model_raises` in `tests/test_ui_actions.py` reuses existing
  `_TREE` widget ID, inherits module-level `pytestmark = [pytest.mark.timeout(60), pytest.mark.agent_e2e]`,
  and follows standard `try`/`finally` + `close_item_view_fixture(root, qapp, _TREE, view_type=QTreeView)`
  lifecycle cleanup.
- All code strictly adheres to flake8 (< 100 chars, no unused imports or variables).

## Missing Tests

| Scenario | Status |
| --- | --- |
| `QTreeView` missing model (by text and index) | Covered (`tests/test_ui_actions.py::test_select_tree_no_model_raises`) |
| Mutation guard sensitivity (guard dropped / reworded) | Covered (`tests/test_ui_actions_tree_no_model_mutation.py`) |
| `QListView` missing model | Covered (`tests/test_ui_actions.py::test_select_list_view_no_model_raises`, PYPOST-972) |
| `QListView` by text / index | Covered (PYPOST-939) |
| List/tree missing option / out of range | Covered (PYPOST-942) |
| Live product `COLLECTION_TREE` e2e missing model | N/A — live product tree always initializes with a model attached |
| Explicit timeout markers | **Present** — module-level `pytest.mark.timeout(60)` |

## Performance Concerns

None. The error-path test is a synchronous fixture interaction that short-circuits immediately
upon verifying `widget.model() is None`, without event loop polling or sleep intervals.

## Deviations from Architecture

None. Implemented exactly as planned in `20-architecture.md`:
- Parametrized over `["Alpha", 0]` with `ids=["by-text", "by-index"]`.
- Teardown handled cleanly via `close_item_view_fixture`.
- Zero production code modified in `pypost/`.

## Follow-up Tasks

### Resolved and Closed Forward

| ID | Origin | Description | Status |
| --- | --- | --- | --- |
| TD-1 | [PYPOST-972](https://pypost.atlassian.net/browse/PYPOST-972) | Dedicated `tree has no model` contract test | **Resolved and closed forward** by PYPOST-1042 via `test_select_tree_no_model_raises` |

### Pre-existing Failures (NON-BLOCKER)

Pre-existing test suite and typecheck failures present on the base commit:

| Issue Key | Area / Node IDs | Classification | Notes |
| --- | --- | --- | --- |
| PYPOST-1231 | Collection tree model edge cases | `NON-BLOCKER — pre-existing` | Pre-existing failure on base commit |
| PYPOST-1232 | Response payload streaming parser | `NON-BLOCKER — pre-existing` | Pre-existing failure on base commit |
| PYPOST-1233 | OAuth token refresh loop | `NON-BLOCKER — pre-existing` | Pre-existing failure on base commit |
| PYPOST-1234 | Environment variable overrides in config | `NON-BLOCKER — pre-existing` | Pre-existing failure on base commit |
| PYPOST-1241 | Type checking baseline gate (`make typecheck`) | `NON-BLOCKER — pre-existing` | Baseline mypy errors tracked separately |

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** (all test modules have explicit 60s timeouts) |
| Deviations from architecture | None |
| Acceptance gaps | **None** — all FR-1..FR-7 and AC-1..AC-8 satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — The tree no-model error path contract is now locked with dedicated parametrized
tests and mutation verification; PYPOST-972 TD-1 is fully closed.
