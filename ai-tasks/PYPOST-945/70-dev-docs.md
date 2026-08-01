# PYPOST-945: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_actions.md` | Fixture keyClicks proof cross-ref for plain/rich editors (PYPOST-945) |
| `doc/dev/testing.md` | Plain/rich keyClicks fixture test note under agent UI action fixtures |

## Not changed

| File | Rationale |
| --- | --- |
| `doc/dev/logging.md` | `via_key_clicks` on fill row already documented (PYPOST-917) |
| `doc/dev/agent_e2e*.md` | No new session API or golden-flow behaviour |

Parent [PYPOST-917/70-dev-docs.md](../PYPOST-917/70-dev-docs.md) already
documented fill DEBUG scalars and default vs keystroke modes. This task adds
plain/rich fixture behavioral coverage; dev docs now point maintainers at the
new tests.

## Template coverage (70-dev-docs.mdc)

- Overview — unchanged (fill primitive already described)
- Architecture — unchanged
- API / Usage — fixture test cross-ref under `ui_fill` logging note
- Configuration — unchanged (none)
- Troubleshooting — unchanged

## Self-Review

- [x] Docs in `doc/dev/`
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] Test-only task — minimal delta, no duplicate API rewrite
