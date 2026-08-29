# PYPOST-1043: Migrate isolated tree harness callers to isolated_tree_actions context manager

## Goals

Isolated collections-tree test harnesses create model-backed `QTreeView` instances for unit and UI interaction testing. PYPOST-973 established shared item-view model detachment via `close_isolated_tree_actions` and introduced the `isolated_tree_actions` context manager helper in `tests/helpers/collections_tree.py`. In PYPOST-973, existing `unittest.TestCase` consumers were updated to register teardown using `build_isolated_tree_actions` + `self.addCleanup(close_isolated_tree_actions, harness)` as a low-churn shortcut, while recording TD-1 to migrate those consumer call sites to the context manager pattern.

The business goal of this task is to improve codebase maintainability, code readability, and call-site consistency across all collection-tree unit test suites by standardizing consumer test cases on the `isolated_tree_actions` context manager. This refactor is purely cosmetic/ergonomic: teardown safety is already guaranteed, and no behavioral or functional changes will be introduced to product runtime or test assertions.

## Programming Language

Python with PySide6 (`pytest` / `unittest` test suites). Documentation and task artifacts are written in English Markdown.

## User Stories

- As a **test maintainer**, I want collection tree test methods to manage harness lifetimes with `with isolated_tree_actions(...) as harness:` instead of separate creation and `addCleanup` calls, so test setup and teardown are idiomatic, concise, and structured.
- As a **developer / code reviewer**, I want consistent fixture lifecycle syntax across all collection tree test modules, so new tests follow a uniform and easily reproducible idiom.
- As a **quality engineer**, I want this test migration to preserve 100% of existing test assertions, execution guarantees, and timeout boundaries without introducing any flaky behavior or regressions in CI.

## Definition of Done

- All consumer test methods in `tests/test_collection_tree_actions.py`, `tests/test_collection_tree_rename_context_menu.py`, `tests/test_collection_tree_delete_confirmation.py`, and `tests/test_collection_tree_rename_delegate_e2e.py` are migrated to use `isolated_tree_actions` context manager blocks.
- Consumer test modules remove unused imports of `build_isolated_tree_actions` and `close_isolated_tree_actions` where no longer directly referenced.
- The low-level helper definitions (`build_isolated_tree_actions`, `close_isolated_tree_actions`, and `isolated_tree_actions`) and their dedicated unit tests in `tests/test_qt_item_view_teardown.py` remain intact and functional.
- All test suites pass cleanly under `make test` and `make check` without Qt warnings or timing regressions.
- No production application code, public APIs, logging schema, or Prometheus metrics are modified.
- Documentation in `doc/dev/testing.md` is updated if necessary to reflect the standardized context manager convention for isolated collection-tree test harnesses.

## Task Description

### Problem

In `tests/test_collection_tree_actions.py` (22 tests), `tests/test_collection_tree_rename_context_menu.py` (8 tests), `tests/test_collection_tree_delete_confirmation.py` (5 tests), and `tests/test_collection_tree_rename_delegate_e2e.py` (1 test), test methods create isolated tree harnesses using:
```python
harness = build_isolated_tree_actions(...)
self.addCleanup(close_isolated_tree_actions, harness)
```
While functional and safe, this two-line pattern is repetitive and less Pythonic than using the `isolated_tree_actions` context manager (`with isolated_tree_actions(...) as harness:`). Migrating consumers to the context manager pattern aligns them with modern Python test conventions and eliminates boilerplate across 36 call sites.

### Business Reason

Uniform and ergonomic test structures lower cognitive overhead for developers extending the collection tree test suite, reduce boilerplate lines of code, and make test scope boundaries visually explicit.

### In Scope

- Migrating consumer test methods in `tests/test_collection_tree_actions.py` to `isolated_tree_actions`.
- Migrating consumer test methods in `tests/test_collection_tree_rename_context_menu.py` to `isolated_tree_actions`.
- Migrating consumer test methods in `tests/test_collection_tree_delete_confirmation.py` to `isolated_tree_actions`.
- Migrating consumer test methods in `tests/test_collection_tree_rename_delegate_e2e.py` to `isolated_tree_actions`.
- Updating imports in migrated test files to import `isolated_tree_actions` instead of `build_isolated_tree_actions` and `close_isolated_tree_actions` (unless direct helper testing requires them).
- Verifying that `tests/test_qt_item_view_teardown.py` retains its explicit tests for both direct and context-manager teardown paths.
- Keeping all existing behavioral test assertions green.
- Updating testing documentation in `doc/dev/testing.md` to reference the preferred context manager idiom.

### Exclusions

- Modifying production UI, widgets, core logic, or public APIs.
- Removing or deprecating `build_isolated_tree_actions` or `close_isolated_tree_actions` in `tests/helpers/collections_tree.py` (they remain foundational building blocks for the context manager and direct unit tests).
- Modifying test helpers or fixtures outside collection tree test harnesses.

## Functional Requirements

- **FR-1:** All collection tree action test cases in `tests/test_collection_tree_actions.py` must instantiate and tear down their test harness using the `isolated_tree_actions` context manager.
- **FR-2:** All rename context menu test cases in `tests/test_collection_tree_rename_context_menu.py` must instantiate and tear down their test harness using the `isolated_tree_actions` context manager.
- **FR-3:** All delete confirmation test cases in `tests/test_collection_tree_delete_confirmation.py` must instantiate and tear down their test harness using the `isolated_tree_actions` context manager.
- **FR-4:** The delegate e2e test case in `tests/test_collection_tree_rename_delegate_e2e.py` must instantiate and tear down its test harness using the `isolated_tree_actions` context manager.
- **FR-5:** Keyword arguments (e.g., `with_rename_delegate=True`) and collection collections input passed to `build_isolated_tree_actions` must be forwarded accurately to `isolated_tree_actions`.
- **FR-6:** The `isolated_tree_actions` helper in `tests/helpers/collections_tree.py` must continue to guarantee proper teardown and model detachment upon block exit (including normal completion and exceptions).
- **FR-7:** All existing assertions in migrated test files must remain unchanged in semantics and verification coverage.

## Non-Functional Requirements

- **NFR-1 — Compatibility:** Pure test-code refactor; zero change to production code, runtime dependencies, or external interfaces.
- **NFR-2 — Reliability & Determinism:** Migrated tests must execute reliably in offscreen Qt mode with explicit timeout decorators (`@pytest.mark.timeout(...)` / `pytestmark`).
- **NFR-3 — Code Cleanliness:** Remove unused imports (`build_isolated_tree_actions`, `close_isolated_tree_actions`) from consumer test files after migration.
- **NFR-4 — Performance:** Zero overhead or slowdown in test execution times across parallel test workers (`make test`).
- **NFR-5 — Observability & Logging:** No changes to production logging or metrics.

## Acceptance Criteria

- **AC-1:** Every test method in `tests/test_collection_tree_actions.py`, `tests/test_collection_tree_rename_context_menu.py`, `tests/test_collection_tree_delete_confirmation.py`, and `tests/test_collection_tree_rename_delegate_e2e.py` that previously called `build_isolated_tree_actions` uses `with isolated_tree_actions(...) as harness:`.
- **AC-2:** No consumer test file contains redundant `self.addCleanup(close_isolated_tree_actions, harness)` calls.
- **AC-3:** Unused helper imports in consumer test files are cleaned up.
- **AC-4:** `tests/test_qt_item_view_teardown.py` continues to pass its unit tests verifying `close_isolated_tree_actions` and `isolated_tree_actions`.
- **AC-5:** Full quality gate `make check` (including `make lint`, `make test`, and `make verify-ai-tasks`) passes with 100% success and no flake.
- **AC-6:** Developer testing documentation (`doc/dev/testing.md`) accurately describes the context manager usage.

## Constraints and Assumptions

- Teardown model detachment logic (`detach_item_view_model`) was implemented in PYPOST-940 and wrapped in `isolated_tree_actions` in PYPOST-973.
- The context manager implementation already handles exception safety via `try ... finally: close_isolated_tree_actions(harness)`.
- The task is cosmetic and refactoring-only; existing test behavior and coverage must be strictly preserved.

## Main Entities and Interactions

| Entity | Role in Test Lifecycle | Required Behavior |
| --- | --- | --- |
| `isolated_tree_actions` | Context manager test helper | Creates harness on enter; closes and detaches model on exit |
| `IsolatedTreeActions` | Test harness data container | Holds view, model, fake request manager, metrics mock, actions |
| Consumer Test Cases | Test units in collection tree suites | Wrap test body inside `with isolated_tree_actions(...) as harness:` |
| `test_qt_item_view_teardown.py` | Teardown regression test suite | Verifies model detachment on harness exit |

## Evidence and Traceability

| Source | Reference Observation | Requirement Trace |
| --- | --- | --- |
| PYPOST-973 TD-1 | Technical debt item recording optional migration to context manager | Goals, AC-1, AC-2 |
| `tests/helpers/collections_tree.py` | `isolated_tree_actions` context manager already implemented and tested | FR-5, FR-6 |
| `tests/test_collection_tree_actions.py` | 22 test methods with `build_isolated_tree_actions` + `addCleanup` | FR-1, AC-1 |
| `tests/test_collection_tree_rename_context_menu.py` | 8 test methods with `build_isolated_tree_actions` + `addCleanup` | FR-2, AC-1 |
| `tests/test_collection_tree_delete_confirmation.py` | 5 test methods with `build_isolated_tree_actions` + `addCleanup` | FR-3, AC-1 |
| `tests/test_collection_tree_rename_delegate_e2e.py` | 1 test method with `build_isolated_tree_actions` + `addCleanup` | FR-4, AC-1 |
| `doc/dev/testing.md` | Testing guide documenting isolated harness teardown | AC-6 |

## Risks and Mitigations

| Risk | Consequence | Mitigation |
| --- | --- | --- |
| Indentation or scope errors in test migration | Test fails prematurely or asserts wrong state | Migrate systematically per test method; run `make test` on modified modules |
| Missing keyword arguments (e.g. `with_rename_delegate`) | Delegate not wired, test failure | Check all `build_isolated_tree_actions` invocations for kwargs and mirror in `isolated_tree_actions` |
| Unused imports triggering lint errors | `make lint` failure | Clean up unused `build_isolated_tree_actions` and `close_isolated_tree_actions` imports |

## Q&A

- **Q: Should `build_isolated_tree_actions` and `close_isolated_tree_actions` be deleted from `tests/helpers/collections_tree.py`?**
  **A:** No. `isolated_tree_actions` internally calls `build_isolated_tree_actions` and `close_isolated_tree_actions`. Furthermore, `tests/test_qt_item_view_teardown.py` directly tests `close_isolated_tree_actions`.
- **Q: Are any production runtime files modified in this task?**
  **A:** No. Only test modules and documentation are touched.
- **Q: Does using a context manager in `unittest.TestCase` methods introduce any issues with `self` or test runner fixtures?**
  **A:** No. `with` statements work seamlessly inside `unittest.TestCase` test methods and cleanly guarantee teardown execution even on assertion failures.
