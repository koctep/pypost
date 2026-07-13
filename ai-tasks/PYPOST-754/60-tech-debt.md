# PYPOST-754: Technical Debt Analysis

**Verdict: SAFE TO CLOSE**

## Shortcuts Taken

- Empty tree shown during load (no explicit "Loading…" placeholder row).
- `load_collections()` synchronous path unchanged for explicit user resync (PYPOST-757 scope).

## Code Quality Issues

None blocking.

## Missing Tooling

- Startup timing span for collection load duration (histogram).
- Graceful shutdown wait for `CollectionStorageGateway` on app quit.

## Performance Concerns

- Background load removes main-thread block at startup (R-P1-002 resolved).
- `refresh_tree` still full rebuild after load (PYPOST-758 follow-up).

## Follow-up Tasks

### Non-blocker: Loading placeholder in tree

- **Priority:** Low
- **Description:** Show a disabled "Loading collections…" row while async load runs.
- **Jira:** (deferred — cosmetic)

### Non-blocker: Gateway shutdown on quit

- **Priority:** Low
- **Description:** Wait for collection worker to finish on application exit, mirroring env gateway
  shutdown debt (PYPOST-508).

### Non-blocker: Startup load duration metric

- **Priority:** Low
- **Description:** Histogram `collection_startup_load_duration_seconds` from dispatch to
  `collections_loaded`.
