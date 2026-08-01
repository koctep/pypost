# PYPOST-917: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/ui_actions.md` | Document `ui_fill(..., via_key_clicks=False\|True)` modes; session mirror; troubleshooting vs `ui_send_key`; DEBUG scalar |
| `doc/dev/logging.md` | Note `via_key_clicks` on fill `ui_action_applied` row |

## Template coverage (70-dev-docs.mdc)

- Overview — existing; fill still part of agent UI actions
- Architecture — architecture table notes `keyClicks`; fill mode note under mermaid
- API / Usage — `ui_fill` rewritten with mode table + logging note; session example
- Configuration — unchanged (none)
- Troubleshooting — keystroke fill vs single-key send clarified

## Self-Review

- [x] Docs in `doc/dev/`
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] FR6: default vs keystroke fill vs `ui_send_key` documented
