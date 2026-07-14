# PYPOST-814: Technical Debt

## Shortcuts Taken

None. Explicit `| None` annotations only; no `# type: ignore` or protocol workarounds.

## Residual Debt

| Item | Severity | Notes |
| --- | --- | --- |
| 41 baseline mypy errors (was 42) | Medium | Parent triage in PYPOST-734 |
| `request_service.py` union-attr (4) | Low | Nullable `TemplateService` in MCP path |
| `request_service.py` var-annotated (2) | Low | Locals in `execute` post-script block |

## Blocker Review

**SAFE TO CLOSE** — protocol alignment complete; worker implicit Optional fixed; baseline updated;
`make check` and `make typecheck` pass.

## Follow-up Tasks

Remaining baseline work is ticketed under parent [PYPOST-734](https://pypost.atlassian.net/browse/PYPOST-734):

| Item | Jira |
| --- | --- |
| R-P2-005c — Type-check pypost/ui incrementally | [PYPOST-815](https://pypost.atlassian.net/browse/PYPOST-815) |

No new follow-ups introduced by this task.
