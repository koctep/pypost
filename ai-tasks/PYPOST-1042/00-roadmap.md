# Roadmap: PYPOST-1042

## Task Metadata

- **Implementation language**: Python (PySide6 / pytest); artifacts and docs in English Markdown

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1042/00-roadmap.md` created from the td-roadmap template
  - [x] `ai-tasks/PYPOST-1042/10-requirements.md` — goals, user stories, FR-1..FR-7,
    NFR-1..NFR-4, constraints, entities, AC-1..AC-8, Q&A
  - [x] Requirements grounded in the real code, not in the ticket text: read
    `tests/test_ui_actions.py:314` (`test_select_list_view_no_model_raises`),
    `_select_tree` / `_select_item_view` in `pypost/agent/ui_actions.py:211-270`,
    `ai-tasks/PYPOST-972/60-tech-debt.md` (TD-1, the origin of this follow-up), and the
    PYPOST-1041 DisplayRole ownership section of `doc/dev/ui_actions.md`
  - [x] **Key factual finding**: `_select_tree` (`pypost/agent/ui_actions.py:243-246`) *already*
    raises `UiTargetNotInteractableError(widget_id, "tree has no model")` when `model()` is
    `None`, as its first statement — before `_pump()` and before the option kind is examined.
    Confirmed at runtime with a throwaway offscreen Qt probe (no repo file written): both a text
    option and an int option raise `reason=tree has no model`. The gap is **test coverage only**;
    no production behaviour is missing. The sole occurrence of the string in `tests/` today is the
    negative assertion at `tests/test_ui_actions.py:328`, inside the item-view test.
  - [x] Consequence recorded in the requirements: the new test is expected green-on-first-run, so
    STEP 3 has no classic red repro and needs mutation-style evidence instead (see FR-6 / AC-7)
  - [x] No test or production code written in this step
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1042/20-architecture.md` — research, implementation plan (with the
    Step 3 failing-repro design), module map, component/interface decisions D-1..D-7,
    AC-1..AC-8 traceability, risks, Q&A
  - [x] **Test location decided**: mirror the twin in place — `test_select_tree_no_model_raises`
    appended to `tests/test_ui_actions.py` next to `test_select_list_view_no_model_raises`
    (shared module `pytestmark = [timeout(60), agent_e2e]`, shared `_TREE` id, shared imports).
    Fixture built inline (`QWidget` + `QHBoxLayout` + model-less `QTreeView`, `set_widget_id`,
    `show()`, `processEvents()`); teardown via the shared
    `close_item_view_fixture(root, qapp, _TREE, view_type=QTreeView)` in `finally`
  - [x] `tests/helpers/collections_tree.py` (`build_isolated_tree_actions` /
    `isolated_tree_actions`) inspected and **rejected with reasons**: it always calls `setModel`,
    never shows the view, sets no `objectName`, and wires a `CollectionTreeActions` presenter —
    it cannot express "no model" and `ui_select` would refuse with `not visible`
  - [x] **AC-4** expressed as `@pytest.mark.parametrize("option", ["Alpha", 0],
    ids=["by-text", "by-index"])` — the module's own idiom (lines 447/473/499/525/601), two
    independently reported items from one body, no duplication
  - [x] **AC-7 technique decided**: PYPOST-1041's AST-parse-hook mechanism does **not** transfer
    (this is runtime Qt behaviour, and a whole mutated `ui_actions` copy would break exception
    class identity); its discipline does. Chosen: mutate `_select_tree` alone via
    `inspect.getsource` → text mutation with a verbatim guard anchor →
    `exec` into a **copy** of `ui_actions.__dict__` → `monkeypatch.setattr(ui_actions,
    "_select_tree", mutant)`; nothing under `pypost/` is written
  - [x] Technique **probe-verified** in the scratchpad (no repo file written): baseline both forms
    → `reason=tree has no model`; guard deleted × text → `reason=option not found: 'Alpha'`;
    guard deleted × index → `AttributeError: 'NoneType' object has no attribute 'rowCount'`;
    reason reworded × both forms → `reason=item view has no model`. Every mutant breaks at least
    one planned assertion
  - [x] **Step 3 plan**: add `tests/test_ui_actions_tree_no_model_mutation.py` *first* (4 items),
    red because the contract test it invokes does not exist yet; Step 4 adds the contract test and
    both files go green — the evidence items green *only because* the new test is sensitive to
    both mutants. "Red" for this coverage-only task is defined in the artifact
  - [x] **AC-8 doc target pinned** (Step 1 review's open flag resolved): no document named
    "agent error-path coverage matrix" exists; the targets are `doc/dev/ui_actions.md`
    § Troubleshooting `tree has no model` bullet (lines 361-365) and the `ui_select`
    fixture-contract paragraph (lines 182-196). `ai-tasks/PYPOST-972/60-tech-debt.md` is **not**
    rewritten — TD-1 closure is recorded forward in this task's `60-tech-debt.md` at Step 7
  - [x] No test or production code written in this step; `pypost/` untouched
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ui_actions_tree_no_model_mutation.py` created containing 4 mutation-evidence items
  - [x] Executed `make test PYTEST_ARGS="tests/test_ui_actions_tree_no_model_mutation.py"` confirming RED failure mode (4 assertion failures because `test_select_tree_no_model_raises` is not yet present in `tests/test_ui_actions.py`)
  - [x] `ai-tasks/PYPOST-1042/25-failing-repro.md` created documenting failing repro run and output
  - [x] No production code in `pypost/` was modified; `tests/test_ui_actions.py` was not modified in Step 3
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Implemented contract test `test_select_tree_no_model_raises` in `tests/test_ui_actions.py` parametrized over `["Alpha", 0]` with `ids=["by-text", "by-index"]`
  - [x] Verified `test_select_tree_no_model_raises` asserts `UiTargetNotInteractableError`, with `"tree has no model"` present and `"item view has no model"` absent
  - [x] Verified inline fixture construction and teardown via `close_item_view_fixture(root, qapp, _TREE, view_type=QTreeView)` in `finally` block
  - [x] Zero production code modifications made (`pypost/` unchanged)
  - [x] Executed `make test PYTEST_ARGS="tests/test_ui_actions.py tests/test_ui_actions_tree_no_model_mutation.py"` confirming all tests in both files are GREEN (including all 4 mutation-evidence items)
  - [x] Executed `make test PYTEST_ARGS="tests/test_display_role_scan_ownership.py tests/test_display_role_scan_ownership_repro.py"` confirming NFR-3 regression suite remains GREEN
  - [x] Executed `make lint` confirming static analysis and documentation checks pass cleanly
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 4 acceptance gate passed (review verdict PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1042/40-code-cleanup.md` created documenting linting, code formatting, cleanup validation, and explicit timeouts
  - [x] Ran `make lint` and flake8 on modified/new test suites (0 errors, 0 warnings)
  - [x] Confirmed all lines <= 100 chars, no unused imports or variables, and explicit timeout markers present
  - [x] Ran `make test PYTEST_ARGS="tests/test_ui_actions.py tests/test_ui_actions_tree_no_model_mutation.py"` confirming test suite passes
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 5 acceptance gate passed (review verdict PASS)
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1042/50-observability.md` created documenting observability review
  - [x] Confirmed test-only scope with zero production code changes
  - [x] Confirmed error propagation observability via `UiTargetNotInteractableError` (`reason="tree has no model"` vs `reason="item view has no model"`)
  - [x] Confirmed bounded test execution with explicit timeouts (`pytestmark = pytest.mark.timeout(60)`)
  - [x] Confirmed no new production logging or metrics are added or required
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 6 acceptance gate passed (review verdict PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1042/60-tech-debt.md` created documenting technical debt analysis, shortcuts taken, test coverage matrix, follow-ups, and closure of PYPOST-972 TD-1
  - [x] Pre-existing test / typecheck failures from base commit (PYPOST-1231, 1232, 1233, 1234, 1241) classified as NON-BLOCKER — pre-existing
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 7 acceptance gate passed (review verdict PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/ui_actions.md` § Troubleshooting to cite dedicated fixture proof `test_select_tree_no_model_raises` (PYPOST-1042) for `tree has no model`
  - [x] Updated `doc/dev/ui_actions.md` § `ui_select` fixture-contract section to document the dedicated tree no-model twin `test_select_tree_no_model_raises`
  - [x] Executed `make lint` confirming flake8, markdown lint, and relative link checks pass cleanly (0 errors)
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 8 acceptance gate passed (review verdict PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1042/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1042/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ui_actions_tree_no_model_mutation.py`
- `ai-tasks/PYPOST-1042/25-failing-repro.md`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1042/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1042/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1042/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
