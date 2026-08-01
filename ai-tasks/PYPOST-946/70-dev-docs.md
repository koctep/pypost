# PYPOST-946: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_actions.md` | Multi-emit `textChanged` proof cross-ref (PYPOST-946) |
| `doc/dev/testing.md` | Line-edit keyClicks emission-count test note |

## Not changed

| File | Rationale |
| --- | --- |
| `doc/dev/logging.md` | `via_key_clicks` on fill row already documented (PYPOST-917) |
| `doc/dev/agent_e2e*.md` | No new session API or golden-flow behaviour |

Parent [PYPOST-917/70-dev-docs.md](../PYPOST-917/70-dev-docs.md) already
documented fill DEBUG scalars and default vs keystroke modes. This task adds
signal-count behavioural coverage; dev docs now point maintainers at the new
test.

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
