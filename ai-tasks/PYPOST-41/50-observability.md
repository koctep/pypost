# PYPOST-41 Observability: Request Logging for History Viewing

## 1. Summary

This document records the logging and metrics additions made during the observability step for
PYPOST-41.  The implementation already contained a solid baseline (load/save logging in
`HistoryManager`, error logging in `RequestService`, and user-action logging in `HistoryPanel`).
This step filled the remaining gaps: mutation-method logging in the data layer, success logging
at the service layer, and two new Prometheus counters that expose history activity through the
existing metrics endpoint.

---

## 2. Logging Additions

### `pypost/core/history_manager.py`

| Method | Level | Message key | Added fields |
|--------|-------|-------------|--------------|
| `append()` | DEBUG | `history_entry_appended` | `method`, `url`, `count` |
| `delete_entry()` | DEBUG | `history_entry_deleted` | `entry_id`, `remaining` |
| `clear()` | DEBUG | `history_cleared` | `count` (entries removed) |

All three mutations were already triggering async saves but emitted no log at the data layer.
The new DEBUG messages allow operators to correlate log lines with file I/O without enabling
INFO-level verbosity in production.

### `pypost/core/request_service.py`

| Location | Level | Message key | Added fields |
|----------|-------|-------------|--------------|
| After `_history_manager.append(entry)` | DEBUG | `history_entry_recorded` | `method`, `url`, `status`, `response_time_ms` |

Previously only the failure path (`history_record_failed`) was logged.  The success path now
produces a DEBUG line that lets developers verify history recording works end-to-end without
inspecting the file on disk.

### `pypost/ui/widgets/history_panel.py`

| Method | Level | Message key | Added fields |
|--------|-------|-------------|--------------|
| `refresh()` | DEBUG | `history_panel_refreshed` | `entry_count` |

Useful when diagnosing UI staleness: confirms whether the panel actually re-read the data after
a request was executed.

### `pypost/ui/presenters/tabs_presenter.py`

| Method | Level | Message key | Added fields |
|--------|-------|-------------|--------------|
| `load_request_from_history()` | INFO | `history_request_loaded_into_editor` | `method`, `url` |

Promoted from UI-only (the panel already logged this) to the presenter layer, which is the
canonical place for user-intent events, consistent with `request_send_initiated` and
`request_finished` already logged there.

---

## 3. Prometheus Metrics Additions

### New counters in `pypost/core/metrics.py` (`MetricsManager._init_metrics`)

| Counter name | Labels | Tracking method | Description |
|--------------|--------|-----------------|-------------|
| `history_entries_appended_total` | `method` | `track_history_entry_appended(method)` | Incremented after every successful `HistoryManager.append()` call |
| `history_entries_loaded_into_editor_total` | — | `track_history_load_into_editor()` | Incremented each time a history entry is loaded into the editor |

### Tracking call sites

| File | Method | Metric tracked |
|------|--------|----------------|
| `pypost/core/request_service.py` | `execute()` — inside history recording block | `history_entries_appended_total[method]` |
| `pypost/ui/presenters/tabs_presenter.py` | `load_request_from_history()` | `history_entries_loaded_into_editor_total` |

Both call sites guard with `if self._metrics:`, consistent with every other tracking call in
the codebase.  No changes to constructor signatures or DI wiring were required.

---

## 4. Rationale for Scope

The following were considered but deliberately excluded:

| Candidate | Reason excluded |
|-----------|-----------------|
| Metrics in `HistoryManager` directly | Would require injecting `MetricsManager` into `HistoryManager`, adding DI complexity with no benefit — the service layer already has metrics. |
| Metrics for `delete_entry` / `clear` | Low operational value; INFO log in `HistoryPanel` already covers the user-visible action. Can be added if a dashboard requirement emerges. |
| Counter for history file load errors | Already covered by `logger.warning("history_manager_load_failed …")` which flows into any log aggregator. |

---

## 5. Verification

Run the test suite to confirm no regressions were introduced:

```
pytest tests/test_history_manager.py tests/test_request_service.py -v
```

Expected: all tests pass.  The new logging and metrics calls are inside already-tested code
paths; no new unit tests are required for the observability layer itself.
