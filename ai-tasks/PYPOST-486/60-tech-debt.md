# PYPOST-486: Technical Debt Analysis

## Shortcuts Taken

- **`_pending_env_manager_refresh` flag** in `EnvPresenter` defers `_on_env_changed` until async
  load completes after the environment manager closes. This bridges the save-then-reload sequence
  without blocking the UI; a cleaner approach would be a single gateway callback for the paired
  save+load workflow.
- **App shutdown with in-flight work** — architecture noted `wait()` or cancel on exit, but
  implementation relies on QObject parentage and process teardown. `handle_exit()` calls
  `QApplication.quit()` without waiting for the gateway worker to finish.
- **Dual-path routing** — sync storage when encryption is disabled, async gateway when enabled.
  Intentional per requirements; adds branching in `load_environments()` and `_save_environments()`.

## Code Quality Issues

- **`save_completed` signal unused** — `EnvironmentStorageGateway` emits it, but `EnvPresenter`
  does not connect. Harmless today (no post-save UI action needed); either wire a handler or
  document that the signal is reserved for future use.
- **`apply_encryption_settings` during in-flight jobs** — fixed: `MainWindow.open_settings()`
  calls `EnvPresenter.wait_storage_idle()` before `apply_encryption_settings()`; gateway exposes
  `has_pending_work()` / `wait_idle()` for main-thread coordination.
- **Per-operation `QThread` subclass** — matches `RequestWorker` precedent; a worker-object +
  `moveToThread` pool would reduce thread churn if operation frequency grows.
- **Gateway unit test reaches private state** — `test_save_coalesces_pending_payload_while_busy`
  sets `gateway._worker` directly instead of driving a real in-flight worker.

## Missing Tests

- No integration test for **encrypted startup ordering** in `MainWindow` (defer
  `tabs.restore_tabs()` / `collections.restore_tree_state()` until `environments_loaded`).
- No test for **env manager close with encryption enabled** exercising
  `_pending_env_manager_refresh` after async save+load.
- No test for **shutdown while the gateway is busy**.
- Responsiveness fixture uses 8 environments × 40 hidden keys — sufficient for CI event-loop
  checks, but not tied to a documented profiling baseline for "large-environment" acceptance.
- `save_completed` presenter wiring untested (signal exists but is unused).

## Performance Concerns

- **Encryption CPU cost unchanged** — work moved off the UI thread; total encrypt/decrypt time
  for large datasets is the same. Per-value overhead remains tracked separately.
  Jira: [PYPOST-485](https://pypost.atlassian.net/browse/PYPOST-485)
- **Save snapshots** — `model_copy(deep=True)` duplicates secret values in memory until the
  worker finishes; acceptable for typical env sizes, worth revisiting if env dictionaries grow
  very large.
- **Single-flight queue** — rapid save then load (e.g. env manager close) serializes operations;
  reload feedback may lag slightly behind the dialog closing, though the UI stays responsive.

## Follow-up Tasks

- Reduce per-value encryption overhead on save/load paths.
  Jira: [PYPOST-485](https://pypost.atlassian.net/browse/PYPOST-485) (non-blocker; orthogonal)
- Extract environment serialization/encryption from `StorageManager` into a dedicated adapter.
  Jira: [PYPOST-482](https://pypost.atlassian.net/browse/PYPOST-482) (non-blocker)
- Add graceful shutdown: wait for `EnvironmentStorageGateway` to finish or cancel before quit
  when encryption is enabled.
  Jira: [PYPOST-508](https://pypost.atlassian.net/browse/PYPOST-508)
- Add `MainWindow` integration test for encrypted async startup gating.
  Jira: [PYPOST-509](https://pypost.atlassian.net/browse/PYPOST-509)
