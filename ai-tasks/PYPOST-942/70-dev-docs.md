# PYPOST-942: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_actions.md` | `ui_select` error `reason=` strings; fixture negative-path test cross-ref (PYPOST-942) |
| `doc/dev/testing.md` | List/tree negative `ui_select` contract tests in `test_ui_actions.py` |

## Not changed

| File | Rationale |
| --- | --- |
| `doc/dev/agent_e2e*.md` | No new session API or golden-flow behaviour |
| `doc/dev/agent_e2e_seed.md` | PYPOST-916 already documents tree select vs click |

Parent [PYPOST-916/70-dev-docs.md](../PYPOST-916/70-dev-docs.md) already
documented `ui_select` for combo/list/tree and troubleshooting for
`option not found` / `option index out of range`. This task only adds test
coverage; dev docs now point maintainers at the four new fixture tests.

## Template coverage (70-dev-docs.mdc)

- Overview — unchanged (select primitive already described)
- Architecture — unchanged
- API / Usage — clarified shared error `reason=` strings on list/tree
- Configuration — unchanged (none)
- Troubleshooting — existing entries retained; test cross-refs added in API section

## Self-Review

- [x] Docs in `doc/dev/`
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] Test-only task — minimal delta, no duplicate API rewrite
