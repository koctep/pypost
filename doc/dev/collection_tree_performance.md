# Collection Tree Performance

This document closes the PYPOST-40 audit performance debt item
([PYPOST-383](https://pypost.atlassian.net/browse/PYPOST-383)). The SOLID audit did **not**
surface new performance-specific findings. Known collection-tree scale behavior was already
tracked in prior tech-debt reports, starting with
[PYPOST-35](https://pypost.atlassian.net/browse/PYPOST-35).

## Audit verdict (PYPOST-40)

| Question | Answer |
| --- | --- |
| New audit-specific performance risks? | **No** |
| Where were tree concerns first filed? | PYPOST-35 performance section |
| What changed since the audit? | Incremental UI paths for delete, rename, and save-as |

For the full audit report see
[ai-tasks/PYPOST-40/30-audit-report.md](../../ai-tasks/PYPOST-40/30-audit-report.md).

## Tree refresh inventory

`CollectionsPresenter.refresh_tree()` clears and rebuilds the entire `QStandardItemModel` from
`RequestManager.get_collections()` — **O(n)** in total requests plus collections.

| User action | UI path | Rebuild scope | Ticket |
| --- | --- | --- | --- |
| App startup | `MainWindow` → `collections.refresh_tree()` once | Full model | — |
| Tab **Save** | `request_saved` → `refresh_tree()` | Full model | Deferred (see below) |
| Tab **Save As** | `request_save_as_completed` → `add_saved_request_to_tree()` | Single node insert | [PYPOST-319](https://pypost.atlassian.net/browse/PYPOST-319) |
| Tree **Delete** | `remove_item_from_tree()`; `refresh_tree()` fallback | Single node or full fallback | [PYPOST-334](https://pypost.atlassian.net/browse/PYPOST-334) |
| Tree **Rename** | `_finish_rename_tree_update()` in-place label sync; fallback | Single label or full fallback | [PYPOST-347](https://pypost.atlassian.net/browse/PYPOST-347) |
| Manual resync | `load_collections()` → disk reload + `refresh_tree()` | Full disk + model | [collection_loading.md](collection_loading.md) |

### Incremental delete (PYPOST-334)

`CollectionTreeActions.handle_delete` calls `CollectionsPresenter.remove_item_from_tree` after a
successful `RequestManager.delete_collection_item`. Full `refresh_tree()` runs only when the
target node cannot be located in the model.

See [collection_item_delete.md](collection_item_delete.md).

### Incremental rename (PYPOST-347)

Rename commit/cancel updates the edited `QStandardItem` label without rebuilding the model.
`refresh_tree()` is used only when the item cannot be found (`collection_item_rename_tree_sync_fallback`).

### Backend delete index (PYPOST-340)

`RequestManager` maintains `_request_index` for O(1) request lookup. Delete paths update the
index incrementally — they do **not** call `_rebuild_index()`. UI incremental delete is
orthogonal but complementary.

## Remaining scale considerations

| Risk | Status | Notes |
| --- | --- | --- |
| Full model rebuild on regular **Save** | **Accepted at current scale** | `main_window_signals.py` wires `request_saved` → `refresh_tree`. Optimize only if profiling on large collections shows user-visible lag. |
| Nested scan in early delete design | **Resolved** | Index-assisted delete ([PYPOST-340](https://pypost.atlassian.net/browse/PYPOST-340)) |
| Full reload on delete (original PYPOST-35 note) | **Resolved** | [PYPOST-334](https://pypost.atlassian.net/browse/PYPOST-334) |

No new Jira follow-up is filed for regular-save full refresh — it is documented here as deferred
work, consistent with [PYPOST-340 tech debt](../../ai-tasks/PYPOST-340/60-tech-debt.md).

## Observability

Existing structured logs distinguish full rebuilds from incremental paths:

| Event | When |
| --- | --- |
| `refresh_tree_completed` | Full model rebuild (`collection_count`, `request_count`) |
| `collection_tree_item_removed` | Incremental delete succeeded |
| `add_saved_request_to_tree_completed` | Incremental save-as insert |
| `collection_item_rename_tree_sync_fallback` | Rename fell back to full rebuild |

Metrics are not added for tree refresh duration in this task; use logs when investigating scale
issues.

## Related

- [Collection Loading](collection_loading.md) — data flow and `refresh_tree` API
- [Collection Item Delete](collection_item_delete.md) — delete and index behavior
- [SOLID Audit](solid_audit.md) — PYPOST-40 summary
- [Technical Debt: PYPOST-40](tech-debt/PYPOST-40.md)
