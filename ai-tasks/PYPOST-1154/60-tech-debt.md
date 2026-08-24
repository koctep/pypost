# PYPOST-1154: Technical Debt

## Follow-ups

None blocking. Operators on high-memory-pressure hosts should continue to tune `WORKERS`
down manually.

## Notes

- Default cap of 16 workers may still be high for Qt-heavy suites on large CPU hosts;
  override via `WORKERS=N` when needed.
- PYPOST-1153 still tracks broader Makefile/orchestrator contract test expansion.

## Jira

No new follow-up issues filed from this task.
