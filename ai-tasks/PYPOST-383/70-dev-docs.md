# PYPOST-383: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/collection_tree_performance.md` | New — audit closure inventory of tree refresh paths |
| `doc/dev/solid_audit.md` | Collection tree performance section (PYPOST-383) |
| `doc/dev/collection_loading.md` | Cross-reference to performance inventory |
| `doc/dev/tech-debt/PYPOST-40.md` | Section 8 — performance concerns closed |
| `tests/test_collection_tree_performance_doc.py` | Guards documented save vs save-as wiring |

## Rationale

The PYPOST-40 audit debt listed performance under "prior reports cover perf" without a single
developer entry point. The new inventory consolidates full vs incremental paths and links to
PYPOST-35-era follow-ups so maintainers do not re-file known tree-scale work.

## Verification

- `pytest tests/test_collection_tree_performance_doc.py -v`
- Jira links in docs resolve to existing tickets.
