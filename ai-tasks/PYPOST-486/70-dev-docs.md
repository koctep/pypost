# PYPOST-486 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-06-11
> Sprint: (current)

---

## 1. What Changed and Why

PYPOST-486 keeps the desktop UI responsive when environment encryption at rest is enabled. Before
this task, `EnvPresenter` called `StorageManager.load_environments()` and `save_environments()`
synchronously on the Qt main thread. Large encrypted datasets blocked the event loop during startup,
environment manager save/reload, variable updates, and collection-driven reloads.

The fix moves encrypt/decrypt and JSON I/O off the UI thread when encryption is enabled, while
preserving atomic save semantics, error dialogs, metrics, and unchanged behavior when encryption is
disabled.

---

## 2. New and Updated Modules

- `pypost/core/environment_storage_worker.py` (new)
  - `EnvironmentStorageWorker(QThread)` — runs one load or save via `StorageManager` on a worker
    thread; emits finished/failed signals.
- `pypost/core/environment_storage_gateway.py` (new)
  - `EnvironmentStorageGateway` — single-flight queue, save coalescing, deep-copy snapshots,
    `wait_idle()` for settings coordination.
- `pypost/ui/presenters/env_presenter.py`
  - Routes async through gateway when `resolve_encryption_enabled()`; sync path when disabled.
  - `environments_loaded` signal; `_apply_loaded_environments()`; save/load failure handlers;
    `_pending_env_manager_refresh` for async env manager close.
- `pypost/ui/main_window.py`
  - Defers `tabs.restore_tabs()` and `collections.restore_tree_state()` until
    `environments_loaded` when encryption is enabled.
  - `open_settings()` calls `env.wait_storage_idle()` before `apply_encryption_settings()`.

`StorageManager` crypto and I/O semantics are unchanged.

---

## 3. Documentation Updated

- `doc/dev/environment_storage_async.md` (new)
  - Overview, architecture diagram, gateway/worker/presenter API, queue/coalesce behavior,
    observability trace, troubleshooting, test commands.
- `doc/dev/environment_encryption_at_rest.md`
  - Cross-links to async doc; component table and data flow note async path; settings apply waits
    for idle; expanded test list.
- `doc/dev/README.md` — navigation entry for async environment storage.
- `doc/dev/architecture.md` — directory entries and Storage bullet for async orchestration.

---

## 4. Configuration Summary

No new settings or environment variables. Async routing follows existing encryption policy
(`env_encryption_enabled` / `PYPOST_ENV_ENCRYPTION_ENABLED`). When encryption is disabled, all
load/save calls remain synchronous.

---

## 5. Testing

Focused suites (43 tests, verified 2026-06-11):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_environment_storage_worker.py \
  tests/test_environment_storage_gateway.py \
  tests/test_env_storage_responsiveness.py \
  tests/test_env_presenter.py
```

Persistence regression:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_storage_environments.py
```

Full regression:

```bash
make test
```

---

## 6. Related Tickets

- `PYPOST-447` — encryption-at-rest foundation.
- `PYPOST-481` — user-facing encryption settings.
- `PYPOST-486` — async encrypted load/save (this task).
- `PYPOST-485` — reduce per-value encryption overhead (orthogonal follow-up).
- `PYPOST-482` — extract storage adapter (orthogonal follow-up).

---

## 7. Review

Documentation prepared per Step 7. Autonomous completion (sprint task runner); user review
optional for wording or additional troubleshooting scenarios.

Verified against implementation: worker/gateway/presenter/main_window modules, observability
artifact (`50-observability.md`), and focused test suite (43 passed).
