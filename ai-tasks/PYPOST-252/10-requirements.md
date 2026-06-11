# PYPOST-252: pytest infrastructure and RequestManager / StateManager unit tests

## Goals

Close the follow-up debt from PYPOST-29/PYPOST-251: ensure PyPost has runnable pytest
infrastructure and adequate automated unit tests for `RequestManager` and `StateManager`, so
manager refactors are regression-safe without manual verification.

## User Stories

- As a **developer**, I want `make test` to run a fast pytest suite so I can verify manager
  behavior locally and in CI.
- As a **maintainer**, I want `RequestManager` CRUD, index, rename, and delete paths covered by
  unit tests with mocked storage so storage I/O does not slow the suite.
- As a **maintainer**, I want `StateManager` persistence, no-op saves, coalescing, debounce, and
  flush semantics covered so UI state regressions are caught early.

## Definition of Done

- [x] Pytest infrastructure documented: `pytest.ini`, `Makefile` (`test`, `test-cov`,
      `venv-test`), `tests/conftest.py` timeout enforcement, `doc/dev/testing.md`.
- [x] `RequestManager` unit tests cover create, save, find, reload, get, delete, rename, and
      index consistency (including edge cases: empty names, not-found, unsupported types).
- [x] `StateManager` unit tests cover expanded collections, open tabs, last environment,
      no-op saves, coalesced saves, immediate `save()`, `flush_pending_save()`, and debounced
      timer persistence.
- [x] All manager tests declare explicit `pytest.mark.timeout` per `do-testing.md`.
- [x] Focused pytest commands documented for maintainers.
- [x] Top-down artifacts stored under `ai-tasks/PYPOST-252/`.

## Task Description

**Source:** `ai-tasks/PYPOST-29/40-tech-debt.md` — follow-up
[PYPOST-252](https://pypost.atlassian.net/browse/PYPOST-252).

**Discovery (2026-06-11):** The repository already satisfies most of this ticket:

| Area | Status |
| --- | --- |
| `pytest.ini` + `pytest-timeout` + coverage gate | Present |
| `make test` / `make test-cov` | Present |
| `tests/test_request_manager.py` | 15 tests (CRUD, index, reload) |
| `tests/test_request_manager_delete.py` | Delete/rename routing |
| `tests/test_settings_persistence.py` | `TestStateManagerPersistence` + ConfigManager |

**Remaining work:** Document the satisfied infrastructure in requirements artifacts; add small
edge-case tests for uncovered branches (empty names, not-found returns, debounced timer path);
update `doc/dev/testing.md` with focused run commands.

**Out of scope:** MainWindow integration tests, presenter-level tests (covered elsewhere),
new pytest plugins, CI workflow changes.

## Q&A

| Question | Answer |
| --- | --- |
| Was pytest missing when PYPOST-29 closed? | Yes — debt note predates PYPOST-88/307/371. Infrastructure now exists. |
| Why not duplicate infrastructure? | Ticket goal is coverage + documentation; re-adding pytest would be redundant. |
| Is 100% line coverage required? | No — adequate unit coverage of public API and error paths is sufficient; achieved ~100% on managers. |
