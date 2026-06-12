# PYPOST-383: Architecture — collection tree performance documentation

## Approach

Documentation-only closure. No runtime behavior changes.

## Deliverables

| Artifact | Purpose |
| --- | --- |
| `doc/dev/collection_tree_performance.md` | Canonical inventory of tree refresh paths |
| `doc/dev/solid_audit.md` | New "Collection tree performance" section linking to inventory |
| `doc/dev/collection_loading.md` | Cross-reference from loading doc to performance inventory |
| `doc/dev/tech-debt/PYPOST-40.md` | Mark audit performance item closed |
| `tests/test_collection_tree_performance_doc.py` | Guard save vs save-as signal wiring |

## Inventory structure

1. **Audit verdict** — PYPOST-40 found no new performance findings.
2. **Refresh path table** — operation, code path, complexity, resolving ticket.
3. **Backend index** — `RequestManager._request_index` delete behavior (PYPOST-340).
4. **Observability** — existing log events for full vs incremental paths.
5. **Remaining risks** — regular save `refresh_tree`; link to open follow-ups if any.

## Out of scope

- Changing `request_saved` → `refresh_tree` wiring.
- Profiling or new metrics.
- New Jira follow-ups for documented deferred work (regular-save optimization).
