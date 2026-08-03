# PYPOST-1044: Code Cleanup Report

## Scope

Reviewed the multi-instance MCP registry, persisted configuration model,
application lifecycle wiring, management dialog, and focused regression tests.

## Cleanup actions

- Kept the registry as the sole lifecycle owner for configured endpoints; no
  new shared mutable server or active-environment path was introduced.
- Tightened reconfiguration preflight: a changed host **or** port is checked
  before stopping the selected running endpoint. This preserves the prior
  endpoint when the replacement bind address is unavailable.
- Made reconfiguration asynchronous and transactional: a candidate endpoint
  must become listening before it replaces the existing runtime; a late bind
  failure retains or restarts the prior endpoint and configuration.
- Deferred `MainWindow` configuration-file persistence for a running-server
  edit until the registry confirms that its replacement endpoint is live.
- Reconcile removed collection/environment references and stop only their
  affected endpoints, so no deleted context continues serving copied data.
- Added focused regression coverage for changed-host preflight, bind-race
  rollback, removed-reference containment, persisted server rows and selected
  UI Start/Stop routing.
- Confirmed configuration and runtime APIs return copied model data where an
  external caller could otherwise mutate a persisted endpoint definition.

## Validation

- [x] `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/test_mcp_server_registry.py tests/test_mcp_servers_dialog.py` — 16 passed.
- [x] Focused MainWindow/registry/dialog suite — 22 passed.
- [x] `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/test_main_window.py tests/test_main_window_shutdown.py tests/test_env_persistence_e2e.py tests/test_apply_settings_font.py tests/test_mcp_server_manager.py` — 31 passed.
- [x] `.venv/bin/python -m flake8 --jobs=1 pypost/` — passed.
- [x] `git diff --check` — passed.

## Independent review

Earlier independent reviews found stale-reference, asynchronous bind rollback,
missing contract coverage, and persistence-before-bind gaps. They were
corrected above. A fresh final reviewer independently passed the resulting
implementation, focused suite (48 passed), flake8, and diff whitespace check.
