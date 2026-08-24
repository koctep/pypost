# PYPOST-1141: Technical Debt Analysis

## Shortcuts Taken

1. **List-copy simulation preserved:**
   - `calculate_batch_evictions` copies `list(self._entries)` and uses `pop(0)` simulation, identical to the pre-refactor `StreamListModel` logic. For standard UI batch sizes (10–100 items) overhead is negligible; deque-index calculation without copying remains a future optimization.

## Code Quality Issues

1. **Repeated UTF-8 encoding for memory accounting:**
   - Both `calculate_batch_evictions`, `apply_batch_evictions`, and `append` call `len(entry.payload.encode("utf-8"))` on each eviction/append. Caching `payload_utf8_bytes` on `StreamEntry` would reduce encoding churn (pre-existing debt from PYPOST-1130).
2. **Plan/apply is not transactional across exceptions:**
   - If `apply_batch_evictions` fails mid-mutation, buffer state could be partial. Current callers (`StreamListModel.append_batch`) invoke apply between Qt signal brackets on the UI thread with no expected exceptions; a future `apply_batch_evictions` could use internal rollback if needed.

## Missing Tests

1. **Large bulk insertion stress:**
   - No new stress test for batches of 10,000+ entries through `calculate_batch_evictions`; existing `TestStreamListModel` covers standard UI sizes.
2. **Cross-thread safety:**
   - `MessageStream` is UI-thread owned; no concurrent mutation tests added (unchanged assumption from WS-3).

## Performance Concerns

1. **O(n) list copy per batch:**
   - Each `calculate_batch_evictions` allocates a Python list copy of the deque. Acceptable for 1 SP refactor; monitor if bulk export paths ever call batch planning.

## Follow-up Tasks

- Optimize `calculate_batch_evictions` to compute eviction indices directly on `deque` without full list copy (deferred from PYPOST-1130 item 4).
- Cache UTF-8 byte size on `StreamEntry` to avoid repeated `encode()` during rapid eviction cycles (pre-existing PYPOST-1130 debt).

## Resolved Debt

- **PYPOST-1130 / PYPOST-1141:** `StreamListModel` no longer accesses `MessageStream._entries` or `MessageStream._retained_bytes`. Eviction math is centralized on `MessageStream.calculate_batch_evictions`.
