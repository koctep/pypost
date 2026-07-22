# Async Environment Storage (Encrypted Load/Save)

## Overview

PYPOST-486 moves encrypted environment load and save off the Qt main thread so the desktop UI stays
responsive when many environments or hidden keys require Fernet encrypt/decrypt work. When
encryption is disabled, behavior is unchanged: `EnvPresenter` calls `StorageManager` synchronously.

Crypto semantics, atomic save guarantees, metrics, and user-visible error handling are preserved.
See [Environment Encryption at Rest](environment_encryption_at_rest.md) for policy, key sources, and
payload format.

## Architecture

```mermaid
flowchart TD
  MW[MainWindow]
  EP[EnvPresenter]
  GW[EnvironmentStorageGateway]
  W[EnvironmentStorageWorker QThread]
  SM[StorageManager]
  File[(environments.json)]

  MW --> EP
  EP -->|"encryption on"| GW
  EP -->|"encryption off"| SM
  GW --> W
  W --> SM
  SM --> File
  W -->|"Qt signals"| GW
  GW --> EP
  EP -->|"environments_loaded"| MW
```

| Component | Module | Responsibility |
| --- | --- | --- |
| Worker | `pypost/core/qt/environment_storage_worker.py` | Runs one load or save on a background `QThread` |
| Gateway | `pypost/core/qt/environment_storage_gateway.py` | Single-flight queue, save coalescing, signal bridge |
| Presenter | `pypost/ui/presenters/env_presenter.py` | Routes sync vs async; applies load results; save errors |
| Startup | `pypost/ui/main_window.py` | Defers tab/tree restore until `environments_loaded` when encrypted |
| Storage | `pypost/core/storage.py` | Unchanged sync encrypt/decrypt and atomic I/O (called from worker) |

### Operation flow (encrypted load)

1. UI calls `EnvPresenter.load_environments()`.
2. Presenter dispatches `EnvironmentStorageGateway.load_async()`.
3. Gateway starts `EnvironmentStorageWorker` if idle; otherwise sets `_pending_load`.
4. Worker calls `StorageManager.load_environments()` off the UI thread.
5. Gateway emits `load_completed` on the main thread.
6. Presenter runs `_apply_loaded_environments()`, then emits `environments_loaded`.

### Queue and coalescing

- **Single-flight:** at most one worker runs at a time.
- **Save coalescing:** if a save is requested while busy, the pending payload is replaced with the
  latest deep-copied snapshot (`model_copy(deep=True)`).
- **Load after save:** a load requested while busy is queued and runs after the current operation
  and any pending save drain.

### Worker finish teardown (PYPOST-829)

When the worker emits `QThread.finished`, `_on_worker_finished`:

1. Captures the finished worker and clears `self._worker`.
2. Calls `deleteLater()` then a short `wait(100)` (`_WORKER_FINISH_WAIT_MS`) so native
   post-`finished` cleanup completes before Python GC can destroy the `QThread`.
3. Drains pending save/load by starting a **new** worker (coalescing / queue semantics
   unchanged).

Dropping the only Python ref without `deleteLater` / short `wait` caused segfaults under
rapid churn + GC (H3). Do not use unbounded `wait()` on the GUI thread. The same pattern
applies to `CollectionStorageGateway` — see [Collection Loading](collection_loading.md).

## API / Usage

### `EnvironmentStorageWorker`

Background thread wrapper around synchronous storage calls.

```python
class EnvironmentStorageWorker(QThread):
    load_finished = Signal(list)
    load_failed = Signal(object)
    save_finished = Signal()
    save_failed = Signal(object)
```

- **load:** `run()` → `storage.load_environments()` → `load_finished` or `load_failed`.
- **save:** `run()` → `storage.save_environments(environments)` → `save_finished` or
  `save_failed`.

Worker objects are created per operation. On `finished`, the gateway schedules
`deleteLater()` and a short `wait(100)` before starting any pending restart (PYPOST-829).

### `EnvironmentStorageGateway`

Owned by `EnvPresenter` (parented to the presenter `QObject`).

```python
gateway = EnvironmentStorageGateway(storage, parent=presenter)
gateway.load_async()
gateway.save_async(environments)  # deep-copied internally

gateway.is_busy() -> bool
gateway.has_pending_work() -> bool
gateway.wait_idle(timeout_ms=30000) -> bool
```

Signals (main thread via queued connections):

- `load_completed(list[Environment])`
- `load_failed(object)`
- `save_completed()` — emitted but not consumed by the presenter today
- `save_failed(object)`

### `EnvPresenter` integration

| Method / signal | Role |
| --- | --- |
| `load_environments()` | Async when `resolve_encryption_enabled(settings)`; else sync |
| `_save_environments()` | Async save when encryption enabled |
| `_apply_loaded_environments()` | Rebuilds env combo and selection |
| `environments_loaded` | Emitted after load UI refresh (sync and async paths) |
| `wait_storage_idle()` | Delegates to gateway; used before applying encryption settings |
| `_pending_env_manager_refresh` | Defers `_on_env_changed` until async reload after env manager close |

Save failure handler shows `QMessageBox.warning` with the exception message. Load failures that
reach the gateway apply an empty environment list and still emit `environments_loaded` so startup
does not hang.

### `MainWindow` startup (encryption enabled)

```python
if resolve_encryption_enabled(self.settings):
    self.env.environments_loaded.connect(self._on_startup_environments_loaded)
    self.env.load_environments()
else:
    self.env.load_environments()
    self.tabs.restore_tabs()
    self.collections.restore_tree_state()
```

When encryption is off, the synchronous sequence is unchanged.

### Settings change coordination

`MainWindow.open_settings()` calls `env.wait_storage_idle()` before
`storage.apply_encryption_settings()` so the worker does not read storage codec state mid-operation.

## Configuration

No new settings or environment variables. Async routing follows existing encryption policy from
[Environment Encryption at Rest](environment_encryption_at_rest.md):

- `AppSettings.env_encryption_enabled` or `PYPOST_ENV_ENCRYPTION_ENABLED`
- Key source chain unchanged

When encryption is disabled, the async gateway is not used.

## Observability

Async orchestration adds structured logs in the worker, gateway, and presenter (see
`ai-tasks/PYPOST-486/50-observability.md`). Storage-layer metrics and logs still emit from
`StorageManager` on the worker thread:

- `environment_value_encryptions_total`
- `environment_value_decryptions_total`
- `environment_encryption_errors_total{stage,reason}`

Trace path: `environment_storage_async_*_dispatched` → gateway queue/coalesce → worker run →
storage encrypt/decrypt counters.

Settings coordination logs (`wait_idle`):

- `environment_storage_gateway_wait_idle_started`
- `environment_storage_gateway_wait_idle_completed` (`elapsed_ms`)
- `environment_storage_gateway_wait_idle_timeout` (`elapsed_ms`) — see Troubleshooting

Worker finish hygiene (PYPOST-829; rare path only):

- `environment_storage_gateway_worker_finish_wait_timeout` (WARNING) —
  `wait_ms`, `pending_save`, `pending_load` — short join after `finished` timed out.
  Happy-path finish is not logged (would spam every load/save).

## Troubleshooting

### UI still feels slow with encryption enabled

**Cause:** PYPOST-486 removes main-thread blocking; total CPU time for Fernet operations is
unchanged. Very large environment sets may still take noticeable wall time before load completes.

**Fix:** monitor worker/storage logs and metrics; per-value overhead is tracked separately in
[PYPOST-485](https://pypost.atlassian.net/browse/PYPOST-485).

### Environment combo empty briefly at startup

**Expected when encryption is enabled.** Tabs and collection tree restore after
`environments_loaded`. Do not call `restore_tabs()` before that signal when testing encrypted
startup.

### Save error dialog but in-memory edits look correct

**Expected.** Failed saves do not replace `environments.json` (atomic `.tmp` + `os.replace` in
`StorageManager`). In-memory state is kept; user must fix the key/config issue and save again.

### Settings change while a save is running

**Mitigation:** `open_settings()` waits for `wait_storage_idle()` before
`apply_encryption_settings()`. External env or registry file changes outside Settings still require
restart or re-apply per encryption-at-rest docs.

### Rapid saves only one write

**Expected.** Coalescing keeps the latest snapshot; intermediate saves while busy are merged.

### Env manager close: selection updates after a short delay

**Expected with encryption on.** Save and reload are serialized on the gateway;
`_pending_env_manager_refresh` applies env-changed signals after async load completes.

### `wait_storage_idle` timeout warning

**Symptoms:** log `environment_storage_gateway_wait_idle_timeout`.

**Cause:** operation exceeded default 30s timeout (large dataset or stuck I/O).

**Fix:** investigate worker/storage logs; avoid calling `apply_encryption_settings` until idle.

### Worker finish wait timeout warning

**Symptoms:** log `environment_storage_gateway_worker_finish_wait_timeout`.

**Cause:** after `QThread.finished`, native cleanup did not finish within
`_WORKER_FINISH_WAIT_MS` (100 ms). Pending restart may still proceed.

**Fix:** triage with pending flags in the log; raise the bound only with field evidence.
Do not convert to unbounded GUI `wait()`. See `ai-tasks/PYPOST-829/50-observability.md`.

### Segfault in `_on_worker_finished` under suite churn

**Cause (historical):** clearing `self._worker` without `deleteLater` / short `wait`
allowed premature `QThread` destruction (PYPOST-829 H3). Fixed in both env and collection
gateways.

**Regression canary:** `tests/test_storage_gateway_h3_stress.py` (≥200 rapid cycles + GC).

## Tests

Focused suites:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_environment_storage_worker.py \
  tests/test_environment_storage_gateway.py \
  tests/test_env_storage_responsiveness.py \
  tests/test_env_presenter.py \
  tests/test_storage_gateway_h3_stress.py
```

### H3 worker-lifecycle canary (PYPOST-829)

`tests/test_storage_gateway_h3_stress.py` runs ≥200 rapid load/save + pending-restart
cycles per gateway with `gc.collect()` between batches. Guards against segfault or
stranded completions after worker finish. Prefer isolation (no heavy suite prefix) when
triaging native crashes — see [gui_testing.md](gui_testing.md).

### Save-completed + widget GC canary (PYPOST-883)

`tests/test_pypost_883_save_async_gc_probe.py` stresses
`EnvironmentStorageGateway.save_async` with ≥200 save-completed waits while
creating/destroying `QComboBox` widgets (`deleteLater` + `gc.collect` between
batches). Investigation outcome: hang **not_reproduced** — no speculative
product/harness lifecycle harden. Treat the module as a permanent cheap canary;
baseline and probe commands live in `ai-tasks/PYPOST-883/30-findings.md`.
See also [gui_testing.md](gui_testing.md) § Bounded nested waits.

### Responsiveness harness hang defense (PYPOST-823 / PYPOST-827 / PYPOST-828)

`tests/test_env_storage_responsiveness.py` waits for gateway `load_completed` /
`load_failed` (and save paths) via a nested `QEventLoop`. The shared helper
`tests.helpers.process_until.process_until` uses a **dual deadline**: a Qt poll timer plus a
daemon `threading.Timer` that posts `loop.quit()` onto the GUI thread with
`QTimer.singleShot(0, loop, loop.quit)`. That guarantees the wait ends within ~`timeout_ms`
even when Qt timer slots never run — a case where `pytest-timeout` SIGALRM alone cannot
interrupt C++ `exec()` and previously stalled the full suite for minutes.

On timeout, the helper raises a **neutral** `AssertionError` (duration + wall-clock reason;
no hard-coded `load_completed/load_failed` wording). Gateway waits pass
`timeout_detail=gateway_timeout_detail(gateway)` so the failure text also includes
`busy=` / `pending=` and optional `worker_running=` at the deadline (PYPOST-828).
For environment gateways, the snapshot also includes `worker_operation=load|save`
when the worker exposes `_operation` (PYPOST-878); collection load-only waits
omit that field.

Hang-regression tests in the responsiveness module prove wall-clock and posted-quit exits.
Sibling gateway/worker modules
(`tests/test_environment_storage_gateway.py`,
`tests/test_collection_storage_gateway.py`,
`tests/test_collection_storage_worker.py`) use the same helper (PYPOST-827) with
domain-appropriate `timeout_detail` wiring (PYPOST-828). Env-presenter async-load
checks in `tests/test_env_presenter.py` also use shared `process_until` (PYPOST-877;
default timeout text, no gateway `timeout_detail`). Gateway and collection-worker `TestCase` modules request the shared suite `qapp`
via `@pytest.mark.usefixtures("qapp")` (PYPOST-830 / PYPOST-884). Presenter
modules (including `tests/test_env_presenter.py`) use the same shared fixture
after PYPOST-886 — do not add a second module-local `QApplication` in
`setUpClass` or a duplicate local `def qapp()`.
Responsiveness uses the `qapp` fixture parameter instead. Details:
[gui_testing.md](gui_testing.md) § Shared `qapp` and § Bounded nested `QEventLoop`
waits.

Persistence and crypto regression (unchanged sync API):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_storage_environments.py
```

Full regression:

```bash
make test
```
