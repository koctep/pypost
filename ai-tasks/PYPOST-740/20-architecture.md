# PYPOST-740: Architecture

## Decision

Rename `request_sync.py` → **`request_persisted_fields.py`**.

Rationale:

- Module exports `copy_request_for_isolated_tab`, `snapshot_persisted_fields`, and
  `persisted_fields_equal` — all operate on `_PERSISTED_FIELD_NAMES`.
- `request_sync` collides conceptually with `MCPServerImpl._execute_request_sync` and HTTP
  execution sync; the new name matches [request_data_copy_policy.md](../../doc/dev/request_data_copy_policy.md).

## Change Surface

| Area | Files |
| --- | --- |
| Core module | `pypost/core/request_persisted_fields.py` |
| UI imports | `tabs_presenter`, `collections_presenter`, `collection_tree_actions`, `request_editor`, `tab_dirty`, `request_save_orchestrator` |
| Tests | `test_request_persisted_fields.py`, `test_tabs_presenter.py` |
| Docs | `architecture.md`, `request_data_copy_policy.md`, `open_request_in_isolated_tab.md`, `mcp_integration.md` |

## Unchanged

- Function names and signatures.
- `_PERSISTED_FIELD_NAMES` tuple.
- `MCPServerImpl._execute_request_sync` naming.
