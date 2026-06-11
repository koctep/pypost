# PYPOST-67: Public env refresh API on EnvPresenter

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Resolve PYPOST-43 TD-2: `MainWindow` must not call private `EnvPresenter._on_env_changed`.
Encapsulate environment refresh behind a stable public API so presenter internals can evolve
without breaking callers.

## Problem statement

After the user saves Settings, `MainWindow.open_settings()` re-applies the active environment
(MCP lifecycle, variable signals, config persistence). Today it reaches into
`EnvPresenter._on_env_changed` and reads `env_selector.currentIndex()` — both internal details.

## User stories

- As a **developer maintaining the UI layer**, I want `MainWindow` to call a documented public
  method on `EnvPresenter` so refactors of env-selection logic do not silently break settings
  apply.
- As a **user saving Settings**, I expect the currently selected environment to stay active with
  variables and MCP state refreshed — unchanged behavior.

## Functional requirements

- **FR-1:** `EnvPresenter` exposes a public method to refresh state for the current combo
  selection (variables, MCP, signals, config save).
- **FR-2:** `MainWindow.open_settings()` uses the new public method instead of `_on_env_changed`.
- **FR-3:** Existing env-selection behavior is unchanged for users.

## Non-functional requirements

- **NFR-1:** Minimal diff; no new logging or metrics required.
- **NFR-2:** Existing tests pass; add or update tests for the public API.

## Out of scope

- Removing `env_selector` and other widget-exposure properties (PYPOST-68 / TD-3).
- Changing when or why settings trigger an env refresh.

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | No external caller invokes `EnvPresenter._on_env_changed` |
| AC-2 | `MainWindow.open_settings` uses the new public API |
| AC-3 | Env refresh behavior unchanged after settings save |
| AC-4 | Affected unit and e2e tests pass |
