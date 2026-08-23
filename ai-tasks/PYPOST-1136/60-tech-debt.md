# PYPOST-1136: Technical Debt Analysis

## Shortcuts Taken

- **Dynamic `__getattr__` Delegation in `MetricsManager` (`pypost/core/qt/metrics.py`)**:
  - *Context*: `pypost/core/qt/metrics.py` has an enforced baseline LOC cap of 185 lines (currently at 183 lines with 2 lines headroom).
  - *Shortcut*: To satisfy the strict file LOC limit without triggering SOLID audit failure, `MetricsManager` utilizes dynamic `__getattr__` delegation to forward all new `track_websocket_*` and `set_websocket_*` calls directly to its internal `self._registry`.
  - *Impact & Tradeoff*: While completely functional and DRY for routing calls from presenters and background workers, dynamic attribute lookups bypass explicit IDE autocompletion and static type checkers on `MetricsManager` itself (though `MetricsProtocol`, `MetricsRegistry`, and `MetricsOTel` retain full static typing).
- **Process-Wide Global Singleton for `SessionSlots` (`pypost/core/websocket_session_policy.py`)**:
  - *Context*: A process-wide coordinator was required across main GUI threads and MCP background threads.
  - *Shortcut*: Exported a default `_GLOBAL_SESSION_SLOTS` singleton via `get_session_slots()`.
  - *Impact & Tradeoff*: Tests must explicitly call `get_session_slots().reset()` or instantiate isolated `SessionSlots()` instances to prevent test state leakage between sequential test runs.

## Code Quality Issues

- **`SettingsDialog` Layout Scaling (`pypost/ui/dialogs/settings_dialog.py`)**:
  - *Issue*: `SettingsDialog` appends configuration sections vertically inside a single scrollable form layout. As settings expand (General, Network, Security, Encryption, WebSocket), the single-column vertical layout becomes long.
  - *Improvement*: Refactoring `SettingsDialog` into a tabbed or side-navigation category layout (e.g. `QTabWidget` or `QListWidget` with stacked pages) would improve maintainability, visual clarity, and UX.
- **Inline Byte and Millisecond Conversions (`pypost/ui/widgets/settings/websocket_section.py`)**:
  - *Issue*: Unit conversions for MiB (`* 1024 * 1024`), KiB (`* 1024`), and seconds/ms are performed inline in spinbox initialization and `collect_fields()`.
  - *Improvement*: Introducing shared unit-formatting and parsing helper functions would centralize value clamping, display formatting, and serialization across all settings section widgets.
- **Presenter Concurrency Slot Guard Lifecycle (`pypost/ui/presenters/websocket_presenter.py`)**:
  - *Issue*: Slot acquisition is invoked in `handle_connect()`, while release is performed conditionally across `_on_state_changed()` (`Idle`, `Closed`, `Failed`) and `teardown()`.
  - *Improvement*: Wrapping slot lifetime in an explicit RAII or session state guard object could encapsulate slot acquisition and release even more cleanly away from UI presentation logic.

## Missing Tests

- **High-Concurrency Stress Benchmarks**:
  - *Scenario*: While multi-threaded concurrent acquire/release is verified with 8 threadpool workers in `tests/test_websocket_settings_and_limits_repro.py::TestWebSocketSessionSlots::test_session_slots_multithreaded_concurrency`, extreme contention tests with 50+ concurrent threads hammering `SessionSlots` under rapid bursts have not been added to standard unit suites to avoid test suite slowdown.
- **Live Disk Settings Persistence End-to-End Test**:
  - *Scenario*: Pydantic schema validation and UI section `collect_fields()` are tested thoroughly in unit tests; however, full round-trip disk write/read to `settings.json` during a mock application restart cycle with live file I/O could be augmented in a dedicated integration test suite.
- **Dynamic Mid-Session Limit Reduction Test**:
  - *Scenario*: Testing the behavior when `ws_max_concurrent_sessions` is reduced dynamically at runtime below the number of currently active sessions (e.g. limit reduced from 8 to 4 while 6 connections are active). Existing sessions are preserved and subsequent connects blocked, but an explicit dedicated scenario test can be added.

## Performance Concerns

- **`SessionSlots` Mutex Lock Contention**:
  - *Concern*: Under normal PyPost GUI usage and moderate probe concurrency (<= 8), `threading.Lock` acquisition overhead is sub-microsecond. However, in hypothetical automated high-throughput fuzzing scenarios where hundreds of MCP probes attempt rapid connects, lock contention could introduce minor serialization latency.
- **Prometheus Metric Exposition Scraping Size**:
  - *Concern*: Adding 9 WebSocket metric families (with discrete label sets like `direction`, `kind`, `reason`, `outcome`) increases the size of Prometheus `/metrics` scrape payloads. Because all labels are strictly bounded to low-cardinality enums, memory footprint remains minimal (< 15 KB overhead).

## Follow-up Tasks

- [PYPOST-1145](https://pypost.atlassian.net/browse/PYPOST-1145): Refactor `SettingsDialog` into a tabbed / categorized layout (`QTabWidget` or `QStackedWidget` navigation) to accommodate growing application preferences.
- [PYPOST-1146](https://pypost.atlassian.net/browse/PYPOST-1146): Implement explicit method definitions and Qt-thread marshaling on `MetricsManager` as part of a planned modularization of `pypost/core/qt/metrics.py`.
- [PYPOST-1147](https://pypost.atlassian.net/browse/PYPOST-1147): Add extreme-concurrency stress benchmark tests for `SessionSlots` slot allocation and contention monitoring under simulated high-thread-count workloads.
- [PYPOST-1137](https://pypost.atlassian.net/browse/PYPOST-1137): Ensure WS-9 (MCP WebSocket Probe Tools) integrates probe execution durations seamlessly with `track_websocket_probe_duration` and `SessionSlots.acquire()` in background worker pools.
