# PYPOST-408: Dev Docs

## Updated Documentation

- Updated `doc/dev/open_request_in_isolated_tab.md` with PYPOST-408 stale-tab sync behavior,
  architecture (`persisted_baseline`, `request_persisted`, `request_sync` helpers), dialog
  flows, save-from-stale guard, logging, troubleshooting, and remaining limitations.

## Key Takeaways

- Documented how overwrite saves broadcast `request_persisted` to sibling tabs and when dialogs
  appear for clean vs dirty tabs.
- Captured `_check_stale_before_save` and overwrite-confirmation behavior when disk is newer
  than a tab baseline.
- Recorded known gaps: left-click shared references (PYPOST-405/406), no persistent stale UI
  indicator, no logging of dialog outcomes, and no detection of out-of-process file edits.

## Follow-ups (no new Jira tickets)

Optional improvements remain in `60-tech-debt.md` (dialog outcome logging, stale banner,
additional unit tests). The PYPOST-405 left-click isolation gap is already tracked under
PYPOST-405 / PYPOST-406.
