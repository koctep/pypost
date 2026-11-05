# PYPOST-1424: Technical Debt Analysis

## Shortcuts Taken

1. **Shared loading chrome for discovery and fetch**:
   Discovery reuses `loading_container` / Cancel rather than a dedicated status strip.
   Concurrent discovery+fetch is unlikely (remotes appear only after discovery), but
   label text and cancel routing must distinguish modes carefully.
2. **Generation discard without transport abort**:
   `ManifestDiscoveryWorker.cancel()` mirrors `CollectionFetchWorker` — sets flags and
   `requestInterruption()`, but sync `list_connections` / `list_manifest_collections`
   I/O is not socket-aborted (covered by existing PYPOST-1425 for fetch; same pattern
   applies to discovery).
3. **Retry button dual-purpose**:
   `retry_fetch_btn` retries either remote collection fetch or manifest discovery
   depending on current selection / library service presence.

## Code Quality Issues

1. Dialog module remains large (~700+ LOC) after PYPOST-1423 extraction; discovery
   handlers added more orchestration in the dialog class.
2. Combo entry shaping (label + `("library", id, path)` tuple) is duplicated between
   worker construction and prior sync code path knowledge — acceptable but could move
   to a tiny shared helper if a third caller appears.

## Missing Tests

1. Explicit automated test for discovery *failure* UI (error banner + retry rediscovery)
   with a raising `list_connections`.
2. Stress: open/close dialog while discovery worker is mid-flight (GC / signal disconnect).
3. Multi-connection catalogs with partial per-connection manifest failures.

## Performance Concerns

1. Discovery still materializes the full catalog entry list in memory before appending
   to the combo — fine for typical library sizes; extreme multi-thousand catalogs may
   want incremental UI appends.
2. `_cancel_discovery_worker` `wait(1000)` on the UI thread during close can stall up to
   1s if remote list calls ignore interruption (same class of issue as fetch cancel).

## Follow-up Tasks

1. **Dedicated discovery status UI (non-blocking strip)**:
   - Suggested SP: 2
   - Separate discovery progress from collection-fetch loading chrome so Cancel and
     labels never share state machines.
   - Jira: [PYPOST-1450](https://pypost.atlassian.net/browse/PYPOST-1450)
2. **Discovery failure + retry automated coverage**:
   - Suggested SP: 1
   - Red/green test for raising `list_connections` showing error_container and retry
     restarting `ManifestDiscoveryWorker`.
   - Jira: [PYPOST-1451](https://pypost.atlassian.net/browse/PYPOST-1451)
3. **Transport-level abort for discovery I/O**:
   - Related: [PYPOST-1425](https://pypost.atlassian.net/browse/PYPOST-1425)
   - Extend abort work to cover `list_connections` / `list_manifest_collections` as well
     as `read_collection`.
4. **`NON-BLOCKER — pre-existing`: Pre-existing lockfile drift**:
   - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
   - Test node: `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
5. **`NON-BLOCKER — pre-existing`: Makefile test suites time out under parallel load**:
   - Jira: [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)
