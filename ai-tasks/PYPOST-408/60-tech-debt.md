# PYPOST-408: Technical Debt Analysis

## Shortcuts Taken

- Stale-tab user choices (Keep draft, Load latest, Dismiss) are not logged; only save cancellation on stale overwrite is logged.
- No persistent visual stale indicator (banner/tooltip) after the dialog is dismissed; `stale_persisted` flag is session-only until reload or save.

## Code Quality Issues

- `snapshot_persisted_fields` deep-copies the full `RequestData` model rather than projecting only `_PERSISTED_FIELD_NAMES`. Comparison uses the field list; behavior is correct today but the helper name oversells filtering.
- `_sync_tab_labels_for_request` is invoked both from `_handle_save_request` and `_on_request_persisted`; idempotent but slightly redundant.

## Missing Tests

- No unit test for `_check_stale_before_save` (user cancels overwrite when `stale_persisted` is set and disk is newer).
- No test asserting clean sibling **Dismiss** sets `stale_persisted` without reloading editor content.
- No test for overwrite confirmation message when disk is newer than tab baseline (non-stale path).

## Performance Concerns

- `persisted_fields_equal` compares all persisted fields including large bodies on every sibling notification. Acceptable for typical requests; consider hashing if duplicate-tab saves become hot paths.

## Follow-up Tasks

- Update `doc/dev/open_request_in_isolated_tab.md` with stale-tab behavior and limitations (Step 7).
- Optional: add INFO logs for stale-tab dialog outcomes if analytics are needed.
- Optional: non-modal stale indicator for tabs with `stale_persisted` set.
- Known PYPOST-405 gap: left-click duplicate tabs may still share one `RequestData` reference; this task helps when ids match across isolated tabs only.
