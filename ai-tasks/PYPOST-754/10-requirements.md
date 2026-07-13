# PYPOST-754: Load collections off main thread at startup

## Goals

PyPost blocks the UI during startup while reading every collection JSON file from disk.
Users with many or large collections experience a frozen window before first paint. This task
removes that main-thread I/O so the application window appears immediately and collections
populate when background loading completes.

## User Stories

- As a PyPost user with many saved collections, I want the app window to open without freezing
  so I can see that the application is starting.
- As a PyPost user, I want my collection tree to populate automatically once loading finishes
  without manual intervention.

## Definition of Done

- [ ] `RequestManager` does not synchronously read collection files during `MainWindow` startup.
- [ ] Collection JSON is loaded on a background thread (worker pattern consistent with
  environment storage).
- [ ] The collection tree shows an empty or loading state until load completes, then refreshes.
- [ ] Tab restoration and tree expansion state wait until collections are in memory.
- [ ] Existing synchronous `reload_collections()` / `load_collections()` paths still work.
- [ ] Unit tests cover worker, gateway, and startup wiring.
- [ ] `make check` passes.

## Task Description

Finding R-P1-002 from PYPOST-689 audit: `RequestManager.__init__` calls synchronous
`load_collections()` which blocks first paint. Remediation: introduce background collection
storage worker and gateway; defer tree refresh until `load_completed`.

## Q&A

- **Why not lazy-load per collection?** Out of scope; full load is required for request index
  and MCP tool discovery at startup.
- **Loading indicator?** Empty tree until refresh is acceptable; optional placeholder row.
