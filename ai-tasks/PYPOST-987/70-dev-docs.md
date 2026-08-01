# PYPOST-987: Developer Documentation

## Summary

Step 8 documents the Import Collection feature for developers and end users. User-facing
guidance lives in `doc/user/collections.md`; implementation detail lives in
`doc/dev/collection_import.md`.

## User documentation

**File:** `doc/user/collections.md`

Added section **Import a collection** covering:

- Entry point: **Import Collection…** below the sidebar tree
- Accepted JSON shape (single object or list; same as `collections/{id}.json`)
- Required/optional fields and MCP tool flags carried through
- Conflict policy: Overwrite, Keep Both, Skip, and apply-to-all
- Result summary dialog and automatic tree refresh
- Notes on overwrite semantics, invalid files, partial parse failures, MCP re-registration,
  and templating placeholders

## Developer documentation

**File:** `doc/dev/collection_import.md` (new)

Covers overview, architecture diagram, plan-then-apply split, conflict and id policy, error
isolation, public API (`load_collection_import_candidates`, `plan_collection_import`,
`apply_imported_collections`, etc.), the `read_import_file` test seam, observability event
names, and a troubleshooting table.

**Index:** `doc/dev/README.md` — **Collection Import** listed under Collections and
environments.

**Cross-links added elsewhere:**

- `doc/dev/collection_storage.md` — points to collection import for the read format
- `doc/dev/ui_identity.md` — `COLLECTION_IMPORT_BUTTON` widget id
- `doc/dev/collection_loading.md` — Related section links to collection import (startup
  shares `apply_loaded_collections`)

## Out of scope for docs

- Postman/Insomnia/OpenAPI converters (explicitly excluded in user doc)
- Export collection (not implemented)
- Environment import/export (separate feature, PYPOST-986)

## Verification

- User doc matches shipped UI strings and conflict vocabulary
- Dev doc matches module layout in `pypost/core/collection_import*.py` and
  `pypost/ui/presenters/collection_import_actions.py`
- No new `doc/dev/` file was required beyond `collection_import.md`; existing collection
  docs were updated only where import touches shared concepts
