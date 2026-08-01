# PYPOST-956: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e_send_settle.md` | Added `wait_response_after_snapshot` API, diagram branch, convention lock command, troubleshooting |
| `doc/dev/agent_e2e_http.md` | Mapping section references shared helper; companion uses helper not inline rewrap |
| `ai-tasks/PYPOST-956/00-roadmap.md` | STEPs 4–8 `[x]` |
| `ai-tasks/PYPOST-956/60-tech-debt.md` | TD-5 Done |

## Template coverage (70-dev-docs.mdc)

- Overview — snapshot helper documented alongside existing text-wait helper
- Architecture — dual-path diagram (text-wait + snapshot)
- API / Usage — `wait_response_after_snapshot` happy path + companion examples
- Configuration — timeout defaults; mapping message prefix
- Troubleshooting — convention lock, `(step)` message contract

## Self-Review

- [x] Docs in `doc/dev/` (two page updates)
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] Mapping Send settle documented with shared helper name
- [x] Text-wait helper contract unchanged

## Worklog

```
tokens_used: 12000
role: execution
step: 8
step_name: Dev Docs
```
