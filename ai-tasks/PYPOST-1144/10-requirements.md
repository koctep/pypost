# PYPOST-1144: WS — Asynchronous background thread processing for stream file export

## Goals

Epic [PYPOST-1123](https://pypost.atlassian.net/browse/PYPOST-1123) (WebSocket Protocol Support) delivers a stream inspector with dual-format transcript export (JSON and Plain Text). When users export large retained buffers (up to 5,000 entries / 64 MiB), synchronous serialization and disk writes on the Qt GUI thread can cause visible UI stutter or frame drops.

This debt item moves stream file export off the UI thread so the stream inspector remains responsive during multi-megabyte exports.

**Implementation language:** Python (PySide6 worker thread in `pypost/core/qt/`, WebSocket stream view in `pypost/ui/`).

## User Stories

- As a **WebSocket power user** exporting a full session transcript, I want the stream inspector UI to stay interactive while the export runs, so that I can continue scrolling, filtering, or pausing display without the application freezing.
- As a **maintainer** following established PyPost async patterns, I want stream export to use the same `QThread` worker approach as collection import and storage gateways, so that threading conventions stay consistent across the UI layer.
- As a **test author**, I want automated verification that export serialization does not monopolize the GUI event loop, so that regressions to synchronous export are caught in CI.

## Definition of Done

The task is considered done when:

1. **Off-thread export**
   - `WebSocketStreamView.export_json()` and `export_text()` schedule transcript formatting and file writes on a background worker thread.
   - A GUI-thread snapshot of stream entries and drop counters is taken before the worker starts so live intake does not race with export.

2. **UI responsiveness**
   - While an export is in progress, the Qt event loop continues processing timers and user input.
   - Export controls indicate busy state and guard against overlapping export requests.

3. **Behavior preservation**
   - Exported JSON and Plain Text files remain Tier 2 sanitized and byte-identical to the prior synchronous export for the same snapshot.
   - Export failure paths still log structured errors without crashing the application.

4. **Automated verification**
   - A dedicated responsiveness test module asserts the GUI thread stays active during a slow export.
   - `make test` and `make lint` pass.

5. **Documentation**
   - Developer docs describe the async export worker and busy-state contract.

## Task Description

### Problem

`WebSocketStreamView.export_json()` and `export_text()` call core export helpers synchronously on the Qt main thread. For maximum-capacity streams this can take 20–50 ms or more on slow disks, blocking paint and input handling. This was recorded in `ai-tasks/PYPOST-1135/60-tech-debt.md` follow-up item 2.

### Scope

**In scope:**

- Background `QThread` worker for JSON and Plain Text stream export triggered from `WebSocketStreamView`.
- GUI-thread snapshot handoff, busy guard, and completion/error signal handling.
- Automated responsiveness tests and developer documentation update.

**Out of scope:**

- Changing export file formats, sanitization tiers, or core formatting logic.
- Progress bars or chunked/cancellable export UX (future enhancement).
- Export from non-UI callers (MCP tools, CLI) — they may continue using synchronous core helpers.

## Q&A

**Q: Should export block until complete when called programmatically?**
A: No — export methods return immediately after starting the worker; callers and tests wait on completion signals or file existence via the event loop.

**Q: Can users start a second export while one is running?**
A: No — overlapping exports are skipped with a busy guard, matching collection import behavior.

**Q: Does live stream intake continue during export?**
A: Yes — only the snapshot at export start is written; new entries after that are excluded from the file (same as a point-in-time export).
