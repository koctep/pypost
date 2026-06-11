# PYPOST-571: Technical Debt

## Verdict

**SAFE TO CLOSE** — proposal complete; implementation deferred to follow-up tickets.

## Follow-up Tasks

| Item | Effort | Jira |
| --- | --- | --- |
| Implement allowlist YAML + `verify_test_log_guardrails.py` + CI step | M | [PYPOST-572](https://pypost.atlassian.net/browse/PYPOST-572) |
| Duration budget audit script + CI annotations | M | [PYPOST-573](https://pypost.atlassian.net/browse/PYPOST-573) |
| `caplog` contract in `do-testing.md` + optional retrofits | S | [PYPOST-574](https://pypost.atlassian.net/browse/PYPOST-574) |
| Reclassify suspicious/unknown ERROR groups from inventory | S | PYPOST-570 / encryption debt |
| Unit tests for guardrail scripts | S | With PYPOST-572 |

## Open questions for implementation

1. **WARNING strictness:** Phase 1 global ceiling vs per-prefix — start with global only.
2. **`log_cli` in CI:** PYPOST-570 may recommend `--log-cli-level=ERROR` override; verifier must
   still see ERROR lines.
3. **asyncio pending-task ERROR:** Single baseline line; investigate root cause before allowlist
   or fix.

## Shortcuts in this task

- PYPOST-569/570 not Done in Jira; duration and `log_cli` sections use Jira descriptions plus
  local `--durations` probe rather than their final artifacts.
