# Uniform Presenter Teardown Contract

## Overview

The UI lifecycle owners use one bounded, idempotent teardown shape for asynchronous work. The
contract covers request tabs, history, encrypted environment storage, and the `MainWindow`
composition root. It fences new work, drains work that was accepted before shutdown, suppresses
late UI delivery, and returns an explicit result to the caller.

The public entry point is:

```python
result = owner.teardown(timeout_ms=5_000)
```

`timeout_ms=None` uses the owner default of 5,000 ms. A supplied value is clamped to zero or
higher. Repeated calls return the same cached `TeardownResult`; teardown is not a retry mechanism.

## Architecture and ownership

| Owner | Public lifecycle API | Work owned or fenced |
| --- | --- | --- |
| `MainWindow` | `teardown(timeout_ms=None)` | Composition root for the child owners below |
| `TabsPresenter` | `begin_teardown()`, `teardown_tab(tab, timeout_ms=None)`, `teardown(timeout_ms=None)` | Request-tab workers, response delivery, chunk buffers, and the environment-update ledger |
| `HistoryPanel` | `teardown(timeout_ms=None)` | Panel callbacks and widget delivery; it does not stop the shared manager |
| `HistoryManager` | `begin_teardown()`, `flush(timeout_ms=None)`, `teardown(timeout_ms=None)` | History load/save threads, accepted writes, and deferred writes |
| `EnvPresenter` | `begin_root_teardown()`, `begin_teardown()`, `teardown(timeout_ms=None)` | Environment UI delivery and the storage gateway |
| `EnvironmentStorageGateway` | `begin_teardown()`, `teardown(timeout_ms=None)`, `wait_idle(timeout_ms=30_000)` | One load/save worker plus queued/coalesced environment work |

`begin_teardown()` is a composition hook that closes admission before a parent starts draining.
It does not produce a result and must be followed by `teardown()` by the owner that is being
closed. `flush(timeout_ms=...)` and `wait_idle()` are bounded synchronization helpers; they are
not substitutes for the public teardown result. `flush(timeout_ms=None)` may wait unboundedly and
must not be used from a deadline-sensitive teardown path.

When encryption is disabled, `EnvPresenter` keeps the existing synchronous `StorageManager` path.
The gateway lifecycle applies to the encrypted asynchronous path.

## `TeardownResult`

`pypost.core.lifecycle.TeardownResult` is a frozen dataclass with these fields:

| Field | Meaning |
| --- | --- |
| `owner` | Stable owner label, such as `request_tab`, `tabs_presenter`, or `main_window`. |
| `outcome` | One of `success`, `incomplete`, or `failed`. |
| `elapsed_ms` | Non-negative elapsed time for the attempt. |
| `active_count` | Active workers or writes observed when teardown was admitted. |
| `pending_count` | Queued work observed at admission. |
| `failure_kind` | `None` on success; normally `timeout`, `worker_error`, or root `owner_failure`. |
| `dispositions` | Optional environment-update sequence-to-disposition diagnostics. |

Outcome semantics:

- `success`: accepted work settled within the deadline and no owner failure was reported.
- `incomplete`: the deadline expired while a worker, write, or queued operation remained. The
  owner may retain that work so it can finish safely, but the cached result is not revised later.
- `failed`: work settled, but an owner reported an operational failure. At the root, any child
  `failed` result produces `failure_kind="owner_failure"` after all children are drained.

The `dispositions` mapping is currently exposed by the tabs result for request-produced environment
updates. Treat it as read-only and copy it if a caller needs a stable diagnostic snapshot; it is
not a persistence API. The current implementation has no public retry/finalization operation for
an `incomplete` result.

## Deadline and shutdown ordering

`MainWindow.teardown()` establishes one deadline for the whole composition. Each child receives a
non-negative remaining budget, and the root drains every available child even if an earlier child
fails. The root calls owners in this order:

1. Mark the root fence and propagate one safe `teardown_id` to its children.
2. Begin teardown for tabs, the history panel, and the history manager. The environment presenter
   receives a root fence through `begin_root_teardown()` so normal UI admission closes early.
3. Teardown request tabs and collection loaders/importers, then the history panel and history
   manager. Collection startup completion is fenced before its storage worker is drained.
4. Before environment teardown, drain request-produced environment updates accepted through the
   tabs cutoff into `EnvPresenter.accept_accepted_env_update()`.
5. Teardown the environment presenter and aggregate child counts and outcomes.

Request workers are asked to stop cooperatively and are waited on in short bounded intervals.
History teardown waits for active writes, an asynchronous load, and the save flush within the same
deadline. Environment teardown pumps the Qt event loop while waiting for the gateway's active and
queued work. The gateway's separate post-`QThread.finished` native cleanup wait is capped at 100 ms;
do not replace it with an unbounded GUI-thread wait.

`shutdown_for_exit()` first flushes the state manager, then runs the 5-second root teardown. On a
successful result it performs the existing encrypted-storage idle check and stops MCP services.
`closeEvent()` and the explicit exit path accept/quit only for `success`; `incomplete` and `failed`
results keep the close event from being accepted.

## Admission cutoff and late-signal fencing

Request-produced environment updates are recorded by `EnvironmentUpdateLedger`. Each accepted
record receives a monotonically increasing sequence and a deep-copied variable snapshot. Root
teardown captures a cutoff sequence:

- Records at or below the cutoff are delivered to the environment consumer and remain observable
  until they reach a terminal disposition.
- Records arriving after the cutoff are recorded as `rejected_after_cutoff` and are not persisted.
- Save coalescing reports the replaced sequence as `coalesced_into_newer_save` rather than silently
  dropping it.

The other owners close admission under their lifecycle locks before taking their teardown snapshot.
Request tabs advance their request generation, claim terminal delivery, fence each tab, and discard
chunk buffers before waiting for workers. Lifecycle-owned history load/save completion callbacks and
environment callbacks check their fence before mutating widgets or presenter state. The
`HistoryPanel._apply_filter()` and `_on_selection_changed()` slots remain UI-local paths; they are
not covered by that lifecycle callback fence and currently require the TD-1256-04 tech-debt caveat
or explicit guarding before making a stronger claim. A late worker or Qt signal may still arrive
after a bounded timeout, but lifecycle-owned callbacks cannot change the cached result or repopulate
a closed UI surface.

## Owner-specific behavior

### Request tabs

Use `teardown_tab()` when removing one request tab; it stops only that tab's request worker and
leaves the workspace alive. Use `TabsPresenter.teardown()` when the tabs owner is closing; it
handles every open `RequestTab`, requests cancellation, suppresses completion/error/chunk delivery,
and drains the accepted environment-update ledger through the configured consumer. Non-request tab
presenters keep their existing teardown seams.

### History panel and persistence

`HistoryPanel.teardown()` disables panel actions and fences lifecycle-owned refresh,
load-completion, and other teardown-controlled widget delivery. The
`_apply_filter()` and `_on_selection_changed()` slots remain UI-local paths and are covered by the
TD-1256-04 tech-debt caveat rather than the lifecycle callback fence. The panel intentionally does
not tear down `HistoryManager`, because the manager is shared with request execution. The root
therefore fences the panel before calling `HistoryManager.teardown()`.

`HistoryManager.teardown()` closes new write admission and drains accepted append, delete, and
clear operations. If an asynchronous load delayed a write, the write is retained and applied after
the load settles before the save drain. `flush(timeout_ms=...)` is the public bounded wait for an
already-started save. `flush(timeout_ms=None)` is also supported by the signature, but may wait
unboundedly because it joins without a timeout; it must not be used from a deadline-sensitive
teardown path. A save error yields `failed` with `failure_kind="worker_error"`; a deadline expiry
yields `incomplete` with `failure_kind="timeout"`.

### Environment presenter and storage

`EnvPresenter` fences UI selection, manager, load, and save callbacks, then delegates its deadline
to `EnvironmentStorageGateway`. The gateway permits one active operation, queues a load, and
coalesces busy saves to the newest deep-copied snapshot. Its `save_outcome` signal associates
accepted sequence IDs with `persisted`, `coalesced_into_newer_save`, `failed`, or `incomplete`.
The legacy `load_completed`, `load_failed`, `save_completed`, and `save_failed` signal signatures
remain unchanged.

Environment load/save signals can be delivered after a timeout because the underlying worker may
finish later. The presenter fence suppresses the UI callback, and the gateway keeps the original
incomplete result terminal. Storage failures that reach an open presenter retain the existing error
handling; late failures after fencing do not open a dialog or mutate the UI.

### MainWindow

`MainWindow` is the UI lifecycle owner. It owns the tabs presenter, history panel, history manager,
and environment presenter, and installs the request-to-environment consumer during composition.
It is responsible for applying the aggregate UI result to the close/exit decision; child owners
must not independently quit the application. The process-level composition root is
`ComposedApp`, documented in [application lifecycle](application_lifecycle.md).

## Logs and metrics

Each owner emits one correlated `lifecycle_teardown_started` and
`lifecycle_teardown_completed` pair per real attempt. The structured fields include the stable
owner, `teardown_id`, deadline/timeout, elapsed duration, and active/pending counts. Admission,
cancellation, and late-delivery records use bounded event names. History I/O failures retain
`load`/`save` operation context.

Prometheus and OpenTelemetry trackers expose the same instruments:

| Metric | Labels / values |
| --- | --- |
| `lifecycle_teardowns_total` | `owner`, `outcome` |
| `lifecycle_teardown_duration_seconds` | `owner`, `outcome` |
| `lifecycle_teardown_active_workers` | `owner`; admission-time active count |
| `lifecycle_teardown_pending_work` | `owner`; admission-time pending count |
| `lifecycle_events_total` | `owner`, `event`: cancellation, admission rejection, or late suppression |
| `environment_update_dispositions_total` | persisted, coalesced, failed, incomplete, or post-cutoff rejection |
| `history_io_failures_total` | `operation`: load or save |

Owners and label values are normalized to fixed allow-lists; unknown values become `unknown`.
Lifecycle logs and metrics must not contain request bodies, URLs, headers, environment values, or
storage payloads. Correlation IDs are opaque identifiers, not user data.

## Compatibility seams

- Metrics are optional at construction time through the existing no-op tracker, so injected test
  doubles and callers without telemetry remain supported.
- `MainWindow` prefers `EnvPresenter.accept_accepted_env_update(variables, sequence)` and falls
  back to the legacy `on_env_update(variables)` callback when composing older doubles.
- Existing environment load/save signal signatures remain compatible; `save_outcome` is the
  additional sequenced lifecycle signal.
- The contract is behavioral and duck-typed rather than a shared base class. New owners and fakes
  must provide `teardown(timeout_ms=None)` and return a result with the fields they expose to the
  composition root.

## Test guidance

The public contract and observability coverage live in:

- `tests/test_presenter_teardown_contract_repro.py` — bounded worker/storage gates, accepted
  persistence, cutoff dispositions, late-signal fencing, owner ordering, shared deadlines, and
  close-event aggregation.
- `tests/test_lifecycle_observability.py` — correlated logs, secret exclusion, Prometheus
  counters/gauges, OpenTelemetry labels, and all environment dispositions.

Use public owner methods and injectable dependency seams. Make asynchronous tests deterministic with
`threading.Event`, Qt signals, and bounded `process_until()` polling; do not use sleeps, `qWait`, or
private worker/gateway state to prove lifecycle behavior. Run the focused suites through the
repository Make target:

```sh
make test WORKERS=1 WORKER_TIMEOUT=60 \
  PYTEST_ARGS='tests/test_presenter_teardown_contract_repro.py tests/test_lifecycle_observability.py'
```

Also run `make lint` and `make verify-ai-tasks` for documentation or lifecycle changes.
