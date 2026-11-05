# PYPOST-1427: Technical Debt Analysis

## Shortcuts Taken

1. **Fixed chunk size / cache depth**:
   - `CHUNK_SIZE = 256` and `MAX_CACHED_CHUNKS = 8` are module constants, not
     tuned from viewport height, DPI, or available RAM.
2. **Catalog still fully resident as domain objects**:
   - Paging bounds `CollectionVariableRowRecord` overhead only. The deserialized
     `Collection.variables` list remains fully in process memory (explicitly out
     of scope for this ticket).
3. **Summary / selected-key APIs remain O(N) scans**:
   - `get_summary_counts`, `get_selected_keys`, and `get_conflict_strategies`
     walk the full variable list with overlay lookups. Acceptable for import
     apply / label refresh; not incremental counters.

## Code Quality Issues

1. **`_variables` alias to mutable collection list**:
   - The model binds `collection.variables` by reference. Concurrent mutation of
     that list while the dialog is open is undefined (same practical risk as
     before when records were built once from a snapshot).
2. **`update_preset` invalidates the entire chunk cache**:
   - Simpler than rewriting candidate fields in every cached record; may cause
     a brief rematerialization hitch on the next paint for large viewports.

## Missing Tests

1. **No automated RSS / tracemalloc assertion for the sub-10MB claim**:
   - Coverage uses logical `cached_record_count` bounds rather than process
     memory sampling (CI variance / allocator noise).
2. **No view-driven scroll prefetch test**:
   - Cache fill is demand-driven from `data()` only; QTableView scroll-prefetch
     behavior is not asserted beyond sparse index access.

## Performance Concerns

1. **Import summary label on every selection change still O(N)** for 100k rows
   if the dialog recomputes `get_summary_counts()` synchronously on each toggle.
2. **First paint after jumping to a cold row** pays one chunk materialization
   (~256 records) on the UI thread — small but measurable vs pure cache hit.

## Follow-up Tasks

1. **Viewport-aware / adaptive chunk sizing for paged variable model**:
   - Priority: Low
   - Suggested SP: **2**
   - Jira: [PYPOST-1458](https://pypost.atlassian.net/browse/PYPOST-1458)
   - Derive `CHUNK_SIZE` / `MAX_CACHED_CHUNKS` from viewport row count and a
     memory budget instead of fixed constants; optional adjacent-chunk prefetch
     on scroll.
2. **Incremental summary counters for extreme catalogs**:
   - Priority: Medium
   - Suggested SP: **3**
   - Jira: [PYPOST-1459](https://pypost.atlassian.net/browse/PYPOST-1459)
   - Maintain running `will_add` / `will_overwrite` / `will_keep` (and selected
     key cardinality) under selection/strategy mutations so the import preview
     label never rescans 100k rows on the UI thread.
3. **Streaming / cursor-backed collection variable source (beyond model records)**:
   - Priority: Low
   - Suggested SP: **8**
   - Jira: [PYPOST-1460](https://pypost.atlassian.net/browse/PYPOST-1460)
   - Avoid retaining the full deserialized `Collection.variables` graph for
     extreme catalogs (true I/O cursor / windowed domain load). Builds on
     PYPOST-1427 model paging.
4. **Process-level memory regression probe for paged model**:
   - Priority: Low
   - Suggested SP: **2**
   - Jira: [PYPOST-1461](https://pypost.atlassian.net/browse/PYPOST-1461)
   - Add an optional/slow CI or benchmark using `tracemalloc` / RSS deltas to
     guard the sub-10MB model-cache claim with allocator-tolerant thresholds.

## Blocker Review (Phase C)

- No BLOCKERs relative to PYPOST-1427 acceptance criteria.
- Verdict: **SAFE TO CLOSE** (commit/Jira close deferred per run instructions).
