# PYPOST-365: GUI test patterns and ResponseView search coverage

## Goals

PYPOST-37 shipped response-body search in the desktop client but deferred automated GUI tests
because the project had no headless Qt test setup. The codebase now runs Qt widget tests with
`QT_QPA_PLATFORM=offscreen` and module-scoped `QApplication` fixtures across many modules.

This task documents those patterns for maintainers and closes the PYPOST-37 follow-up by adding
automated coverage for the ResponseView search bar (type, navigate, match counter, case
sensitivity).

## Programming Language

Python 3.10+

## User Stories

- As a maintainer, I want a single reference for how PyPost GUI tests are structured so new
  widget tests follow the same offscreen Qt conventions.
- As a maintainer, I want ResponseView search behavior covered by automated tests so search
  regressions are caught in CI.
- As a contributor, I want dev docs to explain timeouts, fixtures, and focused test commands
  for Qt modules.

## Definition of Done

- Developer documentation describes GUI test prerequisites, `qapp` fixture usage, offscreen
  platform, and timeout tiers.
- Automated tests cover ResponseView search: typed query, match counter, next/previous
  navigation, case sensitivity, no-match label, and search reset on new response.
- Existing GUI test modules remain green; no new runtime dependency required for local/CI runs.
- PYPOST-37 follow-up item for GUI tests is satisfied.

## Task Description

Source: `ai-tasks/PYPOST-37/60-tech-debt.md` — "Add GUI tests if pytest-qt or xvfb is
introduced to the project." Jira: [PYPOST-365](https://pypost.atlassian.net/browse/PYPOST-365).

### In Scope

- Document current Qt GUI testing approach (offscreen `QApplication`, not full pytest-qt).
- Shared `qapp` fixture in `tests/conftest.py` for new modules.
- `tests/test_response_view_search.py`.
- `doc/dev/gui_testing.md` and `doc/dev/testing.md` cross-link.

### Out of Scope

- Migrating every existing test file to drop local `qapp` fixtures.
- Adding pytest-qt or Xvfb as mandatory dependencies.
- Debounce, lazy match count, or other PYPOST-37 performance follow-ups.
- Full MainWindow integration tests for search.

### Constraints and Assumptions

- CI and `make test` already set `QT_QPA_PLATFORM=offscreen`.
- Tests call widget methods directly; no pixel-level or snapshot testing.
- Module-scoped `qapp` is required because `QApplication` is a process singleton.

## Functional Requirements

- Documentation must list representative GUI test modules and patterns.
- Search tests must assert match counter text (`N of M`, `No matches`) and navigation.
- Tests must declare explicit `pytest.mark.timeout` per project rules.

## Non-functional Requirements

- **Reliability**: tests run headless without display server.
- **Maintainability**: new tests reuse shared `qapp` where possible.
- **CI compatibility**: focused run documented for search tests only.

## Stakeholder Approval

Approved via sprint-task-runner autonomous mode (2026-06-11).
