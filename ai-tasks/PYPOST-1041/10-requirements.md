# PYPOST-1041: Strengthen DisplayRole ownership AST to lock flat finder → display_role_equals

## Goals

In PYPOST-971, shared DisplayRole matching ownership was established between flat item views (`QListView` and similar item views) and tree views by introducing `display_role_equals` and `find_child_index_by_display_text` in `pypost.agent.tree_index`. To prevent regression, an AST test suite (`tests/test_display_role_scan_ownership.py`) was introduced to assert that tree traversal uses `display_role_equals` and `ui_actions._select_item_view` delegates to `find_child_index_by_display_text`.

However, as identified in PYPOST-971 TD-1, the AST convention test currently checks that tree DFS uses the match helper and that `_select_item_view` calls `find_child_index_by_display_text`, but it does not structurally prevent `find_child_index_by_display_text` itself from inlining `ItemDataRole.DisplayRole` comparisons or bypassing `display_role_equals`. Additionally, the public export contract (`__all__`) of `pypost.agent.tree_index` is not asserted by the ownership test suite.

The business and architectural goal of PYPOST-1041 is to harden the architectural boundary tests protecting DisplayRole lookup ownership:
- Prevent silent architectural regressions and duplication where flat child lookup re-inlines Qt DisplayRole extraction and comparison logic.
- Enforce that `find_child_index_by_display_text` delegates row comparison to the canonical `display_role_equals` policy helper.
- Guarantee that `pypost.agent.tree_index` explicitly exports both `display_role_equals` and `find_child_index_by_display_text` in its public module manifest (`__all__`).
- Ensure boundary enforcement is fully automated in fast CI without runtime GUI overhead or timing flakiness.

## Programming Language

Python with PySide6. Task artifacts and documentation use English Markdown.

## User Stories

- As a **PyPost Architecture Guardian**, I want the automated test suite to statically verify that `find_child_index_by_display_text` delegates DisplayRole matching to `display_role_equals` and never accesses `ItemDataRole.DisplayRole` inline, so that matching policy changes can never desynchronize between flat and tree lookups.
- As a **PyPost Architecture Guardian**, I want the ownership suite to verify that `pypost.agent.tree_index` explicitly exports `display_role_equals` and `find_child_index_by_display_text` via `__all__`, so that boundary contracts and public module interfaces remain explicit and guarded against accidental omissions.
- As a **UI Test Maintainer**, I want architectural ownership assertions to execute rapidly in sub-second static analysis without requiring Qt GUI fixture lifecycles or display servers, preserving fast developer feedback loops.
- As a **CI / Release Engineer**, I want architectural boundary tests to include explicit timeout markers following project testing standards (`do-testing`), preventing stalled test runners and ensuring CI stability.
- As a **Developer Documentation Reader**, I want developer guides under `doc/dev/` to accurately describe the AST ownership boundary rules and helper export contracts established for item view matching.

## Task Description

### Problem

In `tests/test_display_role_scan_ownership.py`, AST checks ensure that:
1. `_select_item_view` imports and invokes `find_child_index_by_display_text`.
2. `_select_item_view` does not reference `ItemDataRole.DisplayRole`.
3. `find_tree_index_by_display_text` calls `display_role_equals`.
4. `find_tree_index_by_display_text` does not reference `ItemDataRole.DisplayRole`.

However, the contract for `find_child_index_by_display_text` itself is unconstrained by the AST visitor:
- `find_child_index_by_display_text` could re-inline `index.data(Qt.ItemDataRole.DisplayRole)` without failing the test suite.
- If a future maintainer refactors `find_child_index_by_display_text` to directly extract and compare DisplayRole values, `display_role_equals` would cease to be the single source of truth for exact text matching, reintroducing divergence risk between flat views and recursive trees.
- Furthermore, `pypost.agent.tree_index.__all__` is not validated by the ownership test, leaving module exports unguarded against accidental removal or omissions during refactoring.

### Business Reason

Model-backed item selection is a critical foundation for agent automation and UI end-to-end testing in PyPost. While the implementation in `pypost/agent/tree_index.py` is currently correct and passes runtime tests, convention-enforcing AST tests are the project's primary line of defense against structural architecture erosion. Hardening the ownership test ensures that future refactorings cannot silently reintroduce redundant match logic.

### Scope Boundaries

#### In Scope

- Strengthening `tests/test_display_role_scan_ownership.py` with AST checks verifying that `find_child_index_by_display_text` calls `display_role_equals`.
- Strengthening `tests/test_display_role_scan_ownership.py` with AST checks verifying that `find_child_index_by_display_text` does not access or compare `ItemDataRole.DisplayRole` directly.
- Adding an AST check in `tests/test_display_role_scan_ownership.py` ensuring `__all__` in `pypost.agent.tree_index` explicitly includes `"display_role_equals"` and `"find_child_index_by_display_text"`.
- Preserving all existing AST ownership checks for `_select_item_view` and `find_tree_index_by_display_text`.
- Ensuring test execution complies with `do-testing` requirements (explicit timeout markers, zero live UI/network dependencies).
- Updating developer documentation under `doc/dev/` to describe the tightened ownership assertions and module export guarantees.

#### Non-Goals / Exclusions

- Modifying runtime logic in `pypost/agent/tree_index.py` or `pypost/agent/ui_actions.py` unless necessary to satisfy the contract (both helpers already comply with the target architecture).
- Modifying tree depth-first search semantics, traversal order, or duplicate matching order.
- Changing `ui_select` error types, error messages, logging, or metric payloads.
- Altering combo-box, `QListWidget`, or integer/index-based selection logic.
- Adding runtime Qt GUI tests for contracts already covered by existing integration suites.
- Creating runtime import tests when static AST analysis is sufficient.

## Functional Requirements

- **FR-1:** The ownership test suite must statically inspect the AST of `pypost/agent/tree_index.py` and verify that `find_child_index_by_display_text` calls `display_role_equals`.
- **FR-2:** The ownership test suite must statically inspect the AST of `pypost/agent/tree_index.py` and verify that `find_child_index_by_display_text` does not reference or compare `ItemDataRole.DisplayRole` directly.
- **FR-3:** The ownership test suite must statically inspect the AST of `pypost/agent/tree_index.py` and verify that `__all__` explicitly exports `"display_role_equals"` and `"find_child_index_by_display_text"`.
- **FR-4:** The existing AST assertions verifying that `find_tree_index_by_display_text` calls `display_role_equals` and does not reference `ItemDataRole.DisplayRole` must remain intact and passing.
- **FR-5:** The existing AST assertions verifying that `_select_item_view` in `pypost/agent/ui_actions.py` imports and calls `find_child_index_by_display_text` and does not reference `ItemDataRole.DisplayRole` must remain intact and passing.
- **FR-6:** Canonical developer documentation under `doc/dev/` must document the reinforced AST boundary rules and exported helper requirements.

## Non-Functional Requirements

- **NFR-1 — Performance:** AST test checks must parse source files and evaluate assertions without initializing Qt application runtimes, completing in under 200 milliseconds.
- **NFR-2 — Determinism & Isolation:** Test execution must be strictly deterministic, hermetic, and free from filesystem timing, display server, or network dependencies.
- **NFR-3 — Test Boundedness:** The test file must define explicit timeout protection (`@pytest.mark.timeout(...)` or module-level `pytestmark`) per the `do-testing` standard.
- **NFR-4 — Backward Compatibility:** No public APIs, function signatures, error handling, or runtime behavior of `pypost.agent` modules may be altered.
- **NFR-5 — Code Cleanliness:** All test additions must adhere strictly to flake8 lint rules and type hinting standards.

## Acceptance Criteria / Definition of Done

1. **AC-1 (Flat Finder Match Delegation):** `tests/test_display_role_scan_ownership.py` asserts via AST inspection that `find_child_index_by_display_text` invokes `display_role_equals`.
2. **AC-2 (Flat Finder DisplayRole Exclusion):** `tests/test_display_role_scan_ownership.py` asserts via AST inspection that `find_child_index_by_display_text` contains no references to `ItemDataRole.DisplayRole`.
3. **AC-3 (Explicit `__all__` Manifest):** `tests/test_display_role_scan_ownership.py` asserts via AST inspection that `__all__` in `pypost.agent.tree_index` explicitly includes both `"display_role_equals"` and `"find_child_index_by_display_text"`.
4. **AC-4 (Regression Invariance):** Existing AST ownership assertions for `find_tree_index_by_display_text` and `_select_item_view` remain intact, passing, and unchanged in intent.
5. **AC-5 (Bounded Execution):** The ownership test suite executes with explicit timeout markers per `do-testing` and passes cleanly in fast test runs.
6. **AC-6 (Developer Documentation):** Developer documentation in `doc/dev/` is updated to reflect the reinforced AST ownership and `__all__` boundary rules.
7. **AC-7 (Quality Gates):** `make lint`, `make typecheck`, and `make test` pass without warnings or errors.

## Constraints and Assumptions

- The current implementation in `pypost/agent/tree_index.py` already calls `display_role_equals` inside `find_child_index_by_display_text` and already exports both helpers in `__all__`. Thus, this task is an architectural test hardening debt task that reinforces boundaries against future drift.
- AST parsing using Python's standard `ast` module is the established pattern across `tests/test_*_ownership.py` in this repository.
- Changes are strictly confined to the ownership test file, developer documentation, and workflow artifacts.

## Main Entities and Interactions

| Entity | Role in System | Interactions / Boundary Enforcements |
| --- | --- | --- |
| `display_role_equals` | Canonical match policy | Encapsulates single source of truth for `ItemDataRole.DisplayRole` string matching |
| `find_child_index_by_display_text` | Flat sibling finder | Traverses root or direct child rows; must delegate matching to `display_role_equals` |
| `find_tree_index_by_display_text` | Recursive tree finder | Traverses tree hierarchy; delegates matching to `display_role_equals` |
| `_select_item_view` | UI action controller | Handles item view selection; delegates flat lookup to `find_child_index_by_display_text` |
| `pypost.agent.tree_index.__all__` | Module public interface | Explicitly exports public lookup and match helpers |
| AST Ownership Test Suite | Architecture guardian | Statically verifies call graphs, import delegations, attribute exclusions, and export manifests |

## Q&A

- **Q: Why use an AST test rather than a unit or integration test with mock models?**
  **A:** Runtime behavior is already tested and functioning correctly. An AST test specifically verifies source code structure (architectural boundaries), ensuring developers cannot bypass conventions (e.g. inlining `Qt.ItemDataRole.DisplayRole`) even if the resulting behavior passes functional unit tests.
- **Q: Why should `__all__` be verified in the AST test?**
  **A:** `pypost.agent.tree_index` provides shared utilities consumed across multiple UI action modules. Explicitly checking `__all__` via AST ensures that the public export surface is intentionally declared and protected against accidental omissions during future refactoring.
- **Q: Does this task require modifying `pypost/agent/tree_index.py` or `pypost/agent/ui_actions.py`?**
  **A:** Both modules already conform to the intended architecture. Unless an unexpected discrepancy is found during Step 3/4, the production code is already in compliance; the task's primary deliverable is the hardened test suite and documentation.
- **Q: Does this task impact runtime performance or CI duration?**
  **A:** No. AST parsing of two small Python source files takes only a few milliseconds and runs as part of the fast test suite with a 10-second bounded timeout.
