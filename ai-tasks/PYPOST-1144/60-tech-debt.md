# PYPOST-1144: Technical Debt Analysis

**Verdict:** Async `WebSocketStreamExportWorker` offloads transcript file export from the Qt GUI thread while preserving Tier 2 sanitization and point-in-time snapshots. Responsiveness tests and stream view integration tests pass.
**SAFE TO CLOSE.** Follow-up items below are non-blocking enhancements.

Scope reviewed:
- `pypost/core/qt/websocket_stream_export_worker.py`
- `pypost/core/websocket_stream_export.py` (`StreamExportSnapshot`)
- `pypost/ui/widgets/websocket/stream_view.py`
- `tests/test_websocket_stream_export_responsiveness.py` (3 tests)

---

## Shortcuts Taken

1. **Single in-flight export guard:**
   - Second export requests while busy are skipped with a log line rather than queued.
   - *Improvement:* Optional export queue or cancel button for long-running exports.

2. **No export progress indicator:**
   - Export button disables during work but no progress bar or status message is shown.
   - *Improvement:* Status-bar cue or indeterminate progress for multi-megabyte buffers.

---

## Code Quality Issues

1. **StreamDetailPane private env fallbacks (pre-existing):**
   - `_resolve_export_env()` still reads `_detail_pane._env_vars` / `_hidden_keys` when presenter is unbound.
   - *Improvement:* Public accessors on `StreamDetailPane` (noted in PYPOST-1143 tech debt).

---

## Missing Tests

1. **Concurrent intake during export:**
   - Tests verify off-thread write and GUI responsiveness but do not assert that entries appended after snapshot start are excluded from the export file.
   - *Improvement:* Add explicit snapshot-boundary test.

2. **Text export worker path:**
   - Responsiveness tests patch JSON export; text format uses the same worker but lacks a dedicated slow-path test.
   - *Improvement:* Mirror JSON responsiveness test for `export_text`.

---

## Performance Concerns

None blocking — moving 20–50 ms serialization off the GUI thread addresses the original stutter concern. Worker thread count is one per export (short-lived), matching collection import pattern.

---

## Follow-up Tasks

None ticketed from this task — remaining WS epic items tracked under PYPOST-1123:
- WS-8 TLS — [PYPOST-1131](https://pypost.atlassian.net/browse/PYPOST-1131)
- WS-9 MCP probes — [PYPOST-1137](https://pypost.atlassian.net/browse/PYPOST-1137)

---

## Resolved Debt

- [x] **Asynchronous Stream Export Processing** (PYPOST-1144) — closed by this task; originated from `ai-tasks/PYPOST-1135/60-tech-debt.md` item 2.
