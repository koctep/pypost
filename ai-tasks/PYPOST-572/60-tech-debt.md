# PYPOST-572: Technical Debt

## Verdict

**SAFE TO CLOSE** — Phase 1 guardrails implemented; follow-ups tracked separately.

## Follow-up Tasks

| Item | Jira |
| --- | --- |
| Duration budget audit script + CI annotations | PYPOST-573 |
| `caplog` contract in `do-testing.md` + optional retrofits | PYPOST-574 |
| Reclassify suspicious/unknown ERROR groups from inventory | PYPOST-570 / encryption debt |
| Investigate asyncio pending-task ERROR root cause | Optional hardening |

## Open questions

1. **WARNING strictness:** Phase 1 enforces ERROR only; WARNING ceiling deferred.
2. **Allowlist drift:** Re-run inventory after major test additions; bump baseline if intentional.

## Shortcuts

- Allowlist includes all 72 baseline ERROR patterns (including groups tagged suspicious in
  PYPOST-567) so CI matches current suite behavior; reclassification is separate debt.
