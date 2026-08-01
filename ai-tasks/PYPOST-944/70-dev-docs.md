# PYPOST-944: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_actions.md` | Caplog contract cross-ref for parametrized fill mode proof (PYPOST-944) |
| `doc/dev/testing.md` | Symmetric fill caplog test note under agent UI action fixtures |

## Not changed

| File | Rationale |
| --- | --- |
| `doc/dev/logging.md` | `via_key_clicks` on fill row already documented (PYPOST-917) |
| `doc/dev/agent_e2e*.md` | No new session API or golden-flow behaviour |

Parent [PYPOST-917/70-dev-docs.md](../PYPOST-917/70-dev-docs.md) already
documented fill DEBUG scalars and default vs keystroke modes. This task only
adds symmetric caplog test coverage; dev docs now point maintainers at
`test_ui_action_applied_caplog`.

## Template coverage (70-dev-docs.mdc)

- Overview — unchanged (fill primitive already described)
- Architecture — unchanged
- API / Usage — caplog test cross-ref under `ui_fill` logging note
- Configuration — unchanged (none)
- Troubleshooting — unchanged

## Self-Review

- [x] Docs in `doc/dev/`
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] Test-only task — minimal delta, no duplicate API rewrite
