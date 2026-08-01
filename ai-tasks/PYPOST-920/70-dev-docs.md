# PYPOST-920: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/ui_identity.md` | Add `RESPONSE_STATUS` / `RESPONSE_BODY` to key |
| | identities; note per-tab scope under `ResponseView` |
| `doc/dev/agent_golden_e2e.md` | Document `wait_for_text` settle on status/body |
| | (display-form body); drop sanitize-coupled snapshot |
| | wait as golden primary path |
| `doc/dev/ui_wait.md` | Note golden prefers text-wait on status/body ids |
| `doc/dev/agent_e2e_response_panel.md` | Golden uses text-wait; helpers remain for |
| | sibling walks / excerpts |
| `doc/dev/agent_e2e.md` | Brief note: golden prefers text-wait; panel |
| | helpers still for siblings |
| `ai-tasks/PYPOST-920/00-roadmap.md` | STEP 8 `[x]` |

## Template coverage (70-dev-docs.mdc)

- Overview — existing pages updated; no new standalone page
- Architecture — identity table + golden flow diagram/composition
- API / Usage — golden `wait_for_text` example; identity lookup note
- Configuration — unchanged (none for identities)
- Troubleshooting — golden body form (display vs compact snapshot)

## Self-Review

- [x] Docs in `doc/dev/` (existing files only)
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] FR7: identities listed; golden/agent can wait by id on status/body
- [x] Panel root identity still documented; siblings keep panel helpers
