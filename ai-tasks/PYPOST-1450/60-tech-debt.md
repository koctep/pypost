# PYPOST-1450: Technical Debt Analysis

Technical debt analysis for [PYPOST-1450](https://pypost.atlassian.net/browse/PYPOST-1450):
"[PYPOST-1424] Dedicated discovery status UI separate from fetch loading chrome".

## Resolution of Prior Technical Debt

- **Resolves PYPOST-1424 Technical Debt Item 1**:
  PYPOST-1450 directly resolves Technical Debt Item 1 from [PYPOST-1424](https://pypost.atlassian.net/browse/PYPOST-1424)
  ("Dedicated discovery status UI (non-blocking strip)").
  Catalog manifest discovery and remote collection fetching are now completely decoupled across all UI containers,
  labels, action buttons, and event slots:
  - Discovery status UI: `discovery_container`, `discovery_label`, `cancel_discovery_btn`
  - Discovery error UI: `discovery_error_container`, `discovery_error_label`, `retry_discovery_btn`
  - Fetch loading UI: `loading_container`, `loading_label`, `cancel_loading_btn`
  - Fetch error UI: `error_container`, `error_label`, `retry_fetch_btn`
  - Cancellation & retry slots: `_on_cancel_discovery` / `_on_retry_discovery` vs `_on_cancel_loading` / `_on_retry_fetch`

## Test Timeout Audit (`do-testing` Compliance)

- **Verification**: All 8 tests in [`tests/test_discovery_status_ui_repro.py`](file:///home/src/tests/test_discovery_status_ui_repro.py)
  enforce explicit timeout boundaries:
  - Module-level: `pytestmark = [pytest.mark.timeout(30)]`
  - Function-level: `@pytest.mark.timeout(30)` on all 8 test cases
- **Status**: **NO BLOCKER** — Zero untimed tests introduced. Fully compliant with repository `do-testing` contracts.

## Shortcuts Taken

1. **Inline Error Label Styling**:
   - `self.discovery_error_label.setStyleSheet("color: red;")` was applied directly in
     [`pypost/ui/dialogs/import_collection_variables_dialog.py`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L177)
     to maintain visual parity with the existing `self.error_label.setStyleSheet("color: red;")`.
   - While effective and localized, standard UI architecture would benefit from a shared style
     constant or theme-aware stylesheet rather than hardcoded inline CSS strings.
2. **Direct Dialog Layout Construction**:
   - The discovery status and error container layouts were added directly into `_setup_ui()`
     rather than extracted into a separate compound widget class. This was chosen to minimize churn
     and keep widget hierarchy inspection straightforward for Qt testing.

## Code Quality Issues

1. **Dialog File Length & Single Responsibility**:
   - [`import_collection_variables_dialog.py`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py)
     is ~799 LOC. Although significantly cleaner following the isolation of `ManifestDiscoveryWorker`
     and `CollectionFetchWorker`, the dialog manages two distinct asynchronous state machines
     (manifest discovery and remote collection fetching).
   - If additional background asynchronous operations are added to this or other dialogs, extracting
     a reusable compound widget (e.g. `AsyncStatusStripWidget` providing status label, cancel button,
     error label, and retry button) would reduce boilerplate and enhance testability.
2. **UI Container Boilerplate Duplication**:
   - The structural layout of `discovery_container` (status label + cancel button) and
     `discovery_error_container` (error label + retry button) closely parallels `loading_container`
     and `error_container`. A dedicated compound widget would avoid duplicating container setup.

## Missing Tests

1. **Raising `list_connections` End-to-End Failure Flow**:
   - Automated end-to-end coverage for raising `list_connections` with full UI error banner
     and retry rediscovery is tracked in sibling ticket [PYPOST-1451](https://pypost.atlassian.net/browse/PYPOST-1451).
2. **Partial Multi-Connection Discovery Failures**:
   - Scenarios where one remote connection times out or fails while another succeeds are handled
     by `ManifestDiscoveryWorker` (logs warning, aggregates available entries), but dedicated UI
     repro tests asserting partial warning banners vs hard failure banners could be added.
3. **Rapid Dialog Destruction Stress**:
   - Stress test verifying dialog close / garbage collection while `ManifestDiscoveryWorker`
     is actively streaming catalog results.

## Performance Concerns

1. **Catalog Entry Materialization Before Insertion**:
   - `ManifestDiscoveryWorker` collects all discovered entries into a list before emitting
     `discovery_completed(entries)`. The dialog then clears and repopulates the combo box in a single
     loop. This is fast (< 5ms) and safe for typical workspace/library catalogs (< 1,000 collections),
     but extreme catalogs (10,000+ entries) could cause momentary UI stutter during combo insertion.
2. **Synchronous Worker Cancellation Wait on Close**:
   - `_cancel_discovery_worker` calls `worker.wait(1000)` on the Qt UI thread during dialog close.
     If underlying I/O fails to check interruption promptly, this can stall the UI thread up to 1 second.
     This is addressed by the transport cancellation forwarding ticket [PYPOST-1452](https://pypost.atlassian.net/browse/PYPOST-1452).

## Follow-up Tasks

### Pre-existing Issues

- **`NON-BLOCKER — pre-existing`: Line length violation in test registry**:
  - Jira: [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509)
  - File: `tests/test_mcp_server_registry.py:308` (exceeds 100 characters).
- **`NON-BLOCKER — pre-existing`: Pre-existing lockfile drift**:
  - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
  - Test node: `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
- **`NON-BLOCKER — pre-existing`: Makefile test suites time out under parallel load**:
  - Jira: [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)

### Sibling Follow-up Tasks

- **Discovery failure + retry automated coverage**:
  - Jira: [PYPOST-1451](https://pypost.atlassian.net/browse/PYPOST-1451)
  - Suggested SP: 1
  - Automated repro test for raising `list_connections` showing `discovery_error_container`
    and clicking `retry_discovery_btn` restarting `ManifestDiscoveryWorker`.
- **Forward cancellation through nested get_connection/list_connections**:
  - Jira: [PYPOST-1452](https://pypost.atlassian.net/browse/PYPOST-1452)
  - Suggested SP: 2
  - Socket / transport level abort propagation for background discovery workers.

### Follow-up Debt Items Created

- **[PYPOST-1513](https://pypost.atlassian.net/browse/PYPOST-1513)**:
  - Summary: `[PYPOST-1450] Extract reusable AsyncStatusStripWidget for async UI operations`
  - Scope: Extract compound widget encapsulating progress indicator, status label, cancel button,
    error banner, and retry button for asynchronous UI workflows.
  - Story Points: 2
- **[PYPOST-1514](https://pypost.atlassian.net/browse/PYPOST-1514)**:
  - Summary: `[PYPOST-1450] Centralize dialog stylesheet definitions and error banner theme tokens`
  - Scope: Replace inline `.setStyleSheet("color: red;")` calls with shared UI theme tokens / constants.
  - Story Points: 1
