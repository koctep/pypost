# PYPOST-1143: WS — Expose public env_vars and hidden_keys properties on WebSocketPresenter

## Goals

Epic [PYPOST-1123](https://pypost.atlassian.net/browse/PYPOST-1123) (WebSocket Protocol Support) delivered environment templating and secret masking in [PYPOST-1135](https://pypost.atlassian.net/browse/PYPOST-1135) (WS-7). Child UI widgets (`WebSocketComposer`, `WebSocketStreamView`) currently reach into the presenter's private `_env_vars` and `_hidden_keys` attributes via `getattr` fallbacks.

This follow-up debt item formalizes a stable, read-only public interface so downstream widgets and tests can access the active environment snapshot without depending on private implementation details.

**Implementation language:** Python (PySide6 presenter and widget layer).

## User Stories

- As a **maintainer** extending WebSocket UI widgets, I want `WebSocketPresenter` to expose documented read-only `env_vars` and `hidden_keys` properties, so that child views do not rely on private attribute names that may change during refactors.
- As a **test author** writing headless presenter or widget integration tests, I want a public API for the active environment snapshot, so that assertions and export paths do not use `getattr(presenter, "_env_vars")` workarounds.
- As a **contributor** reading WebSocket architecture docs, I want the presenter environment contract to match the HTTP `EnvPresenter` pattern (`current_variables` / `current_hidden_keys`), so that cross-module conventions stay consistent.

## Definition of Done

The task is considered done when:

1. **Public read-only properties**
   - `WebSocketPresenter` exposes `env_vars -> dict[str, str]` and `hidden_keys -> set[str]` as `@property` accessors.
   - Properties reflect the same snapshots managed by `set_variables()` and `set_hidden_keys()`.

2. **Consumer migration**
   - `WebSocketComposer.send_current_payload()` uses `presenter.env_vars` instead of `getattr(presenter, "_env_vars", ...)`.
   - `WebSocketStreamView.export_json()` and `export_text()` use `presenter.env_vars` and `presenter.hidden_keys` instead of private-attribute `getattr` fallbacks.

3. **Automated verification**
   - A dedicated test module asserts the public properties exist, return expected values, and update after setter calls.
   - `make test` and `make lint` pass.

4. **Documentation**
   - Developer docs describe the public properties as the supported access path for environment snapshots.

## Task Description

### Problem

`WebSocketPresenter` stores environment state in private `_env_vars` and `_hidden_keys` fields. `WebSocketComposer` and `WebSocketStreamView` access these via `getattr(self.presenter, "_env_vars", fallback)` — a coupling noted in `ai-tasks/PYPOST-1135/60-tech-debt.md`.

### Scope

**In scope:**

- Read-only `env_vars` and `hidden_keys` properties on `WebSocketPresenter`.
- Migration of `getattr` fallbacks in `WebSocketComposer` and `WebSocketStreamView`.
- Automated tests and developer documentation update.

**Out of scope:**

- Changing how environment snapshots are propagated from `EnvPresenter` / `TabsPresenter`.
- Altering masking, templating, or stream ingestion behavior.
- Refactoring other presenter duplicate properties (`state` / `_state`, etc.) — tracked separately.

## Q&A

**Q: Should properties return live references or defensive copies?**
A: Return defensive copies (`dict(...)` / `set(...)`) so external callers cannot mutate presenter state without going through `set_variables()` / `set_hidden_keys()`.

**Q: Does this change runtime behavior?**
A: No — same snapshot values are read; only the access path becomes public and typed.
