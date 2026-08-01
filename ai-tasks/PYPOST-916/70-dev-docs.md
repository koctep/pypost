# PYPOST-916: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/ui_actions.md` | Document `ui_select` for combo/list/tree by text or index; troubleshooting for selection vs click |
| `doc/dev/agent_e2e_seed.md` | Note `ui_select` for selection-only on `COLLECTION_TREE` |

## Template coverage (70-dev-docs.mdc)

- Overview — updated in `ui_actions.md`
- Architecture — existing mermaid + table still valid; select dispatch described in API section
- API / Usage — `ui_select` section rewritten with type table + examples
- Configuration — unchanged (none)
- Troubleshooting — wrong-type / option / tree-select-vs-open entries

## Self-Review

- [x] Docs in `doc/dev/`
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] Cross-link seed tree guidance to new API
