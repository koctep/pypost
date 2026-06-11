# PYPOST-47: Developer Documentation

## Purpose

Document the unified collection loading pattern implemented for audit R5 (PYPOST-40).

## New Files

| File | Description |
|------|-------------|
| `doc/dev/collection_loading.md` | RequestManager as single read API for UI |

## Modified Files

| File | Change |
|------|--------|
| `doc/dev/tech-debt/PYPOST-40.md` | Section 3 marked resolved (R5) |
| `doc/dev/solid_audit.md` | R5 note updated |

## Key Takeaways for Developers

- Read collections in UI code via `RequestManager.get_collections()` only.
- Reload from disk via `RequestManager.reload_collections()` only (never `storage.load_collections`
  from UI/presenters).
- Use `CollectionsPresenter.refresh_tree()` when memory is already current.
- Use `CollectionsPresenter.load_collections()` when disk may have changed outside RequestManager.
