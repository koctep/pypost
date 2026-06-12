# PYPOST-127: Optimize request ID lookup in RequestManager

## Goals

Users with large collections need fast request lookup when saving, opening, renaming, or
deleting requests. Linear scans across all collections degrade as request count grows.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a user with many saved requests, I want the app to find a request by ID quickly so
  save and navigation stay responsive.
- As a developer, I want request lookup encapsulated in `RequestManager` so UI code does
  not implement its own search.

## Definition of Done

- `RequestManager.find_request` resolves a request ID in O(1) average time via an
  internal index.
- The index stays consistent after load, save, delete, and rename operations.
- Automated tests cover lookup, reload rebuild, delete consistency, and index usage.
- Developer documentation describes index behavior and maintenance.
- Existing request/collection behavior is unchanged (no UI API changes).

## Task Description

Follow-up from `ai-tasks/PYPOST-14/40-tech-debt.md`. Replace linear request ID search
inside `RequestManager` with a hash map index without changing callers outside the
manager.

### Scope

- In scope: `RequestManager` index, `find_request`, index maintenance on CRUD paths,
  unit tests, dev docs.
- Out of scope: UI tree refresh strategy, storage format, HTTP client changes.

## Q&A

- **Q:** Must the rest of the app change? **A:** No — only `RequestManager` internals
  and tests/docs for this debt item.
- **Q:** Is PYPOST-126 the same work? **A:** Yes — duplicate; close PYPOST-126 when
  PYPOST-127 is done.
