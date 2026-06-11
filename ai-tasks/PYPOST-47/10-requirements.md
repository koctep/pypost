# PYPOST-47: Unify collection loading via RequestManager

## Goals

PyPost users rely on the Collections sidebar to reflect saved requests accurately. When the
application loads or updates collections, every UI surface must read from the same in-memory
source of truth so tabs, the tree, and environment tooling never disagree about what is saved.

The PYPOST-40 audit (R5) found that collection loading bypassed `RequestManager` in some paths,
creating risk of stale or duplicated reads from storage. This task completes the unification so
collection data flows exclusively through `RequestManager.reload_collections()` and
`get_collections()`.

## Programming Language

Python (PySide6 / Qt), consistent with the PyPost desktop application.

## User Stories

- As a **PyPost user**, I want the **Collections tree to match what I just saved**, so I can
  trust the sidebar without manual refresh.
- As a **PyPost developer**, I want **one API for reading collections**, so UI code does not
  call storage directly and tests can mock a single layer.

## Definition of Done

- No UI code path loads collections from `StorageManager` directly; reads go through
  `RequestManager.get_collections()`.
- Disk reloads happen only via `RequestManager.reload_collections()` (not ad-hoc storage calls).
- After in-app CRUD or tab save, the tree refreshes from RequestManager memory without redundant
  disk reload when memory is already current.
- Startup builds the tree from RequestManager state loaded at construction (no double reload).
- Automated tests cover refresh-without-reload and MainWindow startup wiring.
- Developer docs and PYPOST-40 tech-debt entry updated to reflect R5 resolution.

## Task Description

Follow-up from PYPOST-40 audit recommendation R5 (P2). PYPOST-43 moved tree logic into
`CollectionsPresenter` and removed a redundant storage call, but `load_collections()` still
combined disk reload and UI rebuild, and MainWindow invoked that combined method on startup and
after every save. This task separates concerns and routes all collection reads through
RequestManager.

### In Scope

- Split tree refresh from storage reload in `CollectionsPresenter`.
- Update `MainWindow` startup and post-save signal wiring.
- Tests and developer documentation.

### Out of Scope

- Environment loading via storage (separate audit item F10).
- `StorageInterface` abstraction (PYPOST-50).
- Changing RequestManager CRUD semantics.

### Constraints and Assumptions

- `RequestManager.__init__` already calls `reload_collections()` once.
- CRUD methods on RequestManager keep in-memory state synchronized with persisted data.
- External manual edits to collection JSON files are not a supported live-sync scenario.

## Functional Requirements

- UI tree population must use `RequestManager.get_collections()`.
- Full disk resync must use `RequestManager.reload_collections()` only.
- After successful save/rename/delete through RequestManager, tree updates must not require a
  second disk read when memory is authoritative.

## Non-functional Requirements

- **Consistency:** single source of truth for collection data in the running app.
- **Performance:** avoid redundant disk I/O on hot paths (startup, post-save refresh).
- **Testability:** presenters mock RequestManager, not StorageManager, for tree tests.

## Main Entities and Interactions

| Entity | Role |
|--------|------|
| **StorageManager** | Persists collection JSON on disk; accessed only by RequestManager. |
| **RequestManager** | Owns in-memory collections and request index; sole reader of storage for collections. |
| **CollectionsPresenter** | Renders tree from RequestManager; reloads from disk only when explicitly requested. |
| **MainWindow** | Composes presenters; triggers initial tree refresh after RequestManager construction. |

## Q&A

| Question | Answer |
|----------|--------|
| Jira issue | [PYPOST-47](https://pypost.atlassian.net/browse/PYPOST-47) |
| Relation to PYPOST-43? | 43 extracted presenters and removed one storage bypass; 47 completes R5 separation. |
| When is disk reload still needed? | Explicit `load_collections()` (reload + refresh), e.g. user-triggered full resync if added later. |
