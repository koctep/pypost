# PYPOST-1013: Observability Implementation

## Observability Requirements Analysis

| Area | Finding |
| ---- | ------- |
| Key components | `CollectionTreeActions` (menu entry), `CollectionsPresenter` wiring, shared `CollectionExportActions` |
| Critical paths | Context-menu Export → clicked index → same save/write/result as button |
| Performance metrics | Not required — rare user-initiated action (same as PYPOST-989) |

Menu and button share orchestration. Distinguishing the entry point needs a
menu-selection event; outcome/error diagnosis reuses existing
`collection_export_*` logs from PYPOST-989.

## Logging Implementation

### Added Logs

Menu selection (this task / Step 4, module
`pypost.ui.presenters.collection_tree_actions`):

- **INFO**: `collection_export_selected item_type=%s item_id=%s` — user chose
  Export Collection… on a collection or request row (before shared export runs)

Shared export orchestration (unchanged from PYPOST-989, module
`pypost.ui.presenters.collection_export_actions` — covers **both** menu and
button):

- **WARNING**: `collection_export_no_selection` — no exportable collection for
  the resolved index
- **WARNING**: `collection_export_failed reason=%s` — write/serialize error
- **INFO**: `collection_export_completed collection_name=%s request_count=%d path=%s`
  — successful export

Not used for this path: EMERG, ALERT, CRIT, ERR, NOTICE, DEBUG.

### Entry-point distinction

| Trigger | Logs |
| ------- | ---- |
| Context menu | `collection_export_selected` then shared `collection_export_*` |
| Below-tree button | shared `collection_export_*` only (no selection event) |

No `trigger=` field was added on completed/failed lines: the preceding
`collection_export_selected` is enough to attribute menu-driven exports without
duplicating outcome fields.

### Log Structure

- Structured logs: yes (event name + key=value fields)
- Includes context: yes (`item_type`, `item_id`; outcome fields on shared events)
- Log levels: INFO, WARNING
- Large payloads / file contents: not logged

## Metrics Implementation (if applicable)

### Performance Metrics

None. Export remains a rare interactive action; logging suffices (PYPOST-989 /
architecture Q&A).

### Business Metrics

None. Rename/delete use GUI metrics; export (button or menu) does not.

### System Health Metrics

None.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A (no new series; pre-existing scrape unchanged)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A (standard app logs)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (event + key=value; no large structures)
- [x] Metrics are collected correctly — N/A (none added)
- [x] Logging works for menu selection
  (`tests/test_collection_tree_actions.py` —
  `test_collection_export_menu_logs_selected` via `assertLogs`)
- [x] Shared outcome logging still covered
  (`tests/test_collection_export_ui.py` — `collection_export_completed`)
- [x] Large data structures are not logged
- [x] Metrics available for monitoring — N/A for this path

## Notes

Step 6 confirms the menu path is observable without new Prometheus counters.
Operators diagnosing a stuck or failed export from the context menu look for
`collection_export_selected` followed by `collection_export_completed` or
`collection_export_failed` / `collection_export_no_selection`. Button-only
exports omit the selection line.
