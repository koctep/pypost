# PYPOST-1457: Technical Debt Analysis

## Context and Timeout Verification (do-testing)

- **Resolution of Prior Debt**:
  PYPOST-1457 addresses Item 3 from [PYPOST-1426](https://pypost.atlassian.net/browse/PYPOST-1426) ("Slow-drip / delayed-success remote read characterization: Assert loading chrome stays visible and UI remains responsive while a remote read dribbles then completes without error").
- **Automated Testing Timeout Compliance (do-testing)**:
  All 10 tests in `tests/test_remote_collection_slow_drip_repro.py` declare an explicit per-test timeout via module-level `pytestmark = [pytest.mark.timeout(30)]`.
  - The entire test suite completes in ~4.8s (average < 0.5s per test), well within the 30-second budget.
  - Verification: **No Blocker**.
- **Pre-existing Timeout / Infrastructure Issues**:
  Tracked under pre-existing test timeout debt [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413) (27 legacy test files missing explicit `pytestmark` markers).

---

## Shortcuts Taken

1. **Monolithic In-Memory Return in `SlowDripSimulator`**:
   `SlowDripSimulator` slices time using small sleep intervals (`slice_interval_s=0.02s`) while checking `CancellationToken` before returning a pre-constructed `Collection` object all at once. It does not stream raw byte chunks or yield partial JSON tokens incrementally.
2. **Duplicated Test Polling and Wait Helpers**:
   `tests/test_remote_collection_slow_drip_repro.py` defines local `_wait_for_manifest_discovery` and `_wait_for_fetch_idle` loop utilities, mirroring routines in `test_remote_collection_fault_injection_repro.py` and `test_variable_import_virtualization_repro.py`. Consolidating shared dialog test wait helpers is already tracked under [PYPOST-1455](https://pypost.atlassian.net/browse/PYPOST-1455).
3. **Static Loading Label State**:
   `ImportCollectionVariablesDialog.loading_label` displays static text ("Loading collection from library...") without dynamic elapsed time, byte counts, or transfer rates during slow reads.

---

## Code Quality Issues

1. **Coarse Signal Granularity on `CollectionFetchWorker`**:
   `CollectionFetchWorker` exposes only terminal signals (`fetch_completed(object, int)` and `fetch_failed(Exception, int)`). There is no incremental progress signal (such as `fetch_progress(bytes_read, total_bytes)` or `fetch_chunk_received(int)`) to notify the UI of mid-stream transfer activity.
2. **Direct Event Attribute Inspection in Test Doubles**:
   Tests inspect internal `threading.Event` objects (`sim.entered`, `sim.completed`, `sim.cancelled`) directly on `SlowDripSimulator`. Exposing explicit query properties or wait methods would improve encapsulation.

---

## Missing Tests

1. **Multi-Worker Rapid Consecutive Collection Switches Stress Test**:
   `test_slow_drip_supersession_on_collection_change` verifies switching once from Collection A to Collection B. Rapid successive switches across 5+ collections in quick succession (<10ms intervals) under active slow drips are not yet stress-tested to guarantee thread pool and worker reference cleanup under rapid churn.
2. **Chunked Stream Delivery Callback Simulation**:
   `SlowDripSimulator` pauses in time slices and returns the whole `Collection`. Real chunked/streaming HTTP responses deliver partial bytes or partial variables incrementally. Simulating partial byte/variable chunk delivery callbacks would allow testing mid-stream progress indicators.
3. **Large Payload (10,000+ Variables) Slow-Drip Transfer**:
   The current suite tests small-to-medium variable payloads (0 to 2 variables). A test evaluating slow-drip delivery of a large collection (thousands of variables) would verify UI responsiveness during table batching and deserialization following a slow-drip transfer.

---

## Performance Concerns

1. **Synthetic Delay Accumulation in Suite Runtime**:
   Each slow-drip test case introduces deliberate real-time delays (0.2s–0.35s). Running 10 test cases currently takes ~4.8s. Expanding this matrix without careful bounded slice tuning could increase test suite duration.
2. **Qt Event Loop Polling Frequency**:
   Test assertions poll the event loop with `time.sleep(0.01)` to `0.02s` slices. Under heavily saturated CI environments, scheduling latencies could increase wait times, though bounded timeouts (5.0s wait deadlines) prevent hangs.

---

## Follow-up Tasks

### Pre-existing Issues (`NON-BLOCKER — pre-existing`)

1. **Lockfile drift**:
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
   - Test node: `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`

2. **Makefile test suites time out under parallel load**:
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)
   - Scope: Makefile test suites timing out intermittently under high parallel CI load; legacy test files missing explicit timeout markers.

### Proposed Technical Debt Items

#### Item 1: `SlowDripSimulator` Chunked Stream Callback Simulation
- **Title**: `SlowDripSimulator` chunked stream callback simulation
- **Type / Severity**: Minor / Testing Improvement
- **Jira**: [PYPOST-1524](https://pypost.atlassian.net/browse/PYPOST-1524)
- **Suggested Story Points**: 2 SP
- **Description**: Currently `SlowDripSimulator` pauses in time slices and then returns the whole `Collection` at once. Real chunked/streaming HTTP responses deliver partial bytes or partial variables incrementally.
- **Potential Impact**: Tests cannot verify mid-stream progress events, chunk parsing errors, or partial payload decoding behaviors.
- **Suggested Remediation**: Extend `SlowDripSimulator` with an optional `chunk_callback` or generator yielding partial byte chunks/variables at each time slice.

#### Item 2: UI Progress Bar / Byte Counter During Slow Drips
- **Title**: UI progress bar / byte counter during slow drips
- **Type / Severity**: Minor / UX Enhancement
- **Jira**: [PYPOST-1525](https://pypost.atlassian.net/browse/PYPOST-1525)
- **Suggested Story Points**: 3 SP
- **Description**: Currently `loading_label` displays static text "Loading collection from library...". For multi-megabyte collections or slow connections, users receive no visual feedback on transfer volume.
- **Potential Impact**: Users on slow connections may wonder whether the transfer has stalled or is actively receiving data.
- **Suggested Remediation**: Add a `fetch_progress(bytes_read, total_bytes)` signal to `CollectionFetchWorker` and connect it to a dynamic progress indicator or byte counter in `ImportCollectionVariablesDialog.loading_container`.

#### Item 3: Automated Test for Multi-Worker Rapid Consecutive Collection Switches
- **Title**: Automated test for multi-worker rapid consecutive collection switches under slow drips
- **Type / Severity**: Minor / Concurrency Stress Test
- **Jira**: [PYPOST-1526](https://pypost.atlassian.net/browse/PYPOST-1526)
- **Suggested Story Points**: 2 SP
- **Description**: `test_slow_drip_supersession_on_collection_change` tests switching once (A -> B). Testing rapid switching across 5+ collections in rapid succession under slow drips would stress-test thread pool / worker cleanup and generation counter race resistance.
- **Potential Impact**: Edge-case race conditions in rapid collection switching could potentially leak worker threads or cause stale generation race issues.
- **Suggested Remediation**: Add an automated stress test in `tests/test_remote_collection_slow_drip_repro.py` that rapidly flips `collection_combo` across 5+ items while each previous worker is mid-drip, verifying all superseded workers terminate and only the final collection renders.

#### Item 4: Consolidate Shared Qt Dialog Wait Helpers (Already Ticketed)
- **Title**: Shared Qt idle-wait helper for import-dialog tests
- **Status**: Open
- **Jira**: [PYPOST-1455](https://pypost.atlassian.net/browse/PYPOST-1455)
- **Suggested Story Points**: 2 SP
- **Description**: Extract `_wait_for_manifest_discovery` and `_wait_for_fetch_idle` helpers into `tests/helpers/qt_dialog_waits.py` to eliminate duplication across `test_remote_collection_fault_injection_repro.py`, `test_variable_import_virtualization_repro.py`, and `test_remote_collection_slow_drip_repro.py`.
