# PYPOST-801: Migrate startup/shutdown legacy log strings in main.py

## Goals

Close PYPOST-747 tech-debt follow-up by replacing Pattern C lifecycle sentences in
`pypost/main.py` with structured logging event names per `doc/dev/logging.md`.

## User Stories

- As an operator, I want startup and shutdown log lines to use stable `app_startup` /
  `app_shutdown` event names, so log aggregation and grep rules match the documented catalog.
- As a maintainer, I want `main.py` lifecycle logs aligned with PYPOST-747 conventions, so
  remaining legacy migration debt in the composition root is cleared.

## Definition of Done

| ID | Criterion |
| --- | --- |
| AC-1 | `logger.info("PyPost starting up")` replaced with `app_startup` |
| AC-2 | `logger.info("PyPost shutting down")` replaced with `app_shutdown` |
| AC-3 | `doc/dev/logging.md` Application lifecycle catalog reflects migrated events |
| AC-4 | `make check` passes |

## Out of scope

- Migrating other legacy lifecycle strings (`metrics_server`, `mcp_server`, etc.)
- Adding key=value context fields to startup/shutdown (no variables today)
- CI allowlist changes (INFO-level only; no allowlist entry)

## Source

- Parent: [PYPOST-747](https://pypost.atlassian.net/browse/PYPOST-747)
- Tech debt: `ai-tasks/PYPOST-747/60-tech-debt.md` line 18
