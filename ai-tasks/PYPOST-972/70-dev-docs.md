# PYPOST-972: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_actions.md` | Cross-ref `test_select_list_view_no_model_raises`
  (PYPOST-972); troubleshooting for `item view has no model` + fixture proof;
  add sibling `tree has no model` troubleshooting entry (was production-only) |
| `doc/dev/testing.md` | Note item-view no-model contract test alongside PYPOST-942
  negatives |

## Not changed

| File | Rationale |
| --- | --- |
| `doc/dev/agent_e2e*.md` | No product `QListView` golden flow; fixture coverage only |
| `doc/dev/agent_lifecycle.md` | Session helpers / API surface unchanged |

## Template coverage (70-dev-docs.mdc)

- Overview — select primitive already described (PYPOST-939); no rewrite
- Architecture — unchanged
- API / Usage — contract-test cross-ref under `ui_select`
- Configuration — unchanged (none)
- Troubleshooting — `item view has no model` retained + test pointer; `tree has
  no model` documented for FR-4 distinctness

## Self-Review

- [x] Docs in `doc/dev/`
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] Test-only task — minimal delta; locked reason wording unchanged
- [x] FR-6 / AC-6 — troubleshooting remains consistent with production reasons
