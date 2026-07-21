# PYPOST-831: Dev Docs Update

## Changes

Updated `doc/dev/request_actions.md` (extends PYPOST-824 prior art):

- Plus-placeholder section: document shared `_ensure_current_is_navigable` used by
  both `close_tab` (PYPOST-824) and `close_tabs_for_request_ids` (PYPOST-831);
  bulk preferred index is left of the leftmost closed tab.
- Testing table: added
  `test_close_tabs_for_request_ids_rightmost_does_not_land_on_plus` and
  `test_close_tabs_for_request_ids_multiple_rightmost_does_not_land_on_plus`.
- Troubleshooting “Closing a request tab leaves focus on `+`”: point at the
  shared helper and list bulk-close callers / regression tests.

Updated `doc/dev/collection_item_delete.md`:

- Architecture: note that post-delete bulk tab close reselects a navigable
  request tab (link to Request Actions).
- Testing: tab-closure row mentions rightmost / multiple-rightmost land-on-plus
  coverage (PYPOST-831).

## Validation

- [x] Docs match production `_ensure_current_is_navigable` / bulk-close behavior
- [x] Bulk land-on-plus regression test names listed
- [x] No separate new Architecture doc needed beyond these updates
