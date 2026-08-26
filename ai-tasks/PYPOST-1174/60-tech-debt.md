# PYPOST-1174: Technical Debt Analysis

## Shortcuts Taken

1. **Jira apply is orchestrator-owned.** Exact PYPOST-1155 `summary` / labels
   live in `20-architecture.md`. This ticket's execution agents do not call
   Jira MCP for the epic rename. Until the orchestrator applies that payload,
   live Jira may still show the old WebSocket-only title.
2. **Historical "either works" text kept in PYPOST-1164 architecture.**
   `ai-tasks/PYPOST-1164/20-architecture.md` still records the original
   deferral. Requirements and tech-debt files now state option (a). The old
   sentence is history, not a second live decision.
3. **No automated test** that Jira title, labels, and docs stay in sync.
   This is a planning ticket; there is no red test (Step 3 N/A).

## Code Quality Issues

None introduced. No `pypost/` code changed.

Pre-existing: `make lint-docs` does not cover `doc/dev/` or `ai-tasks/`.
That gate is owned by PYPOST-1020's user-guide linter, not this ticket.

## Missing Tests

None for this ticket. No pytest files. Timeout markers do not apply.

## Performance Concerns

None. Documentation and Jira fields only.

## Follow-up Tasks

No new Debt tickets from this step.

- Confirm orchestrator applied PYPOST-1155 summary
  `Tab protocol modes — blank-tab protocol selector` and unioned labels
  `mcp`, `ux`, `documentation` (keep `websocket`). Not a product defect if
  apply is still pending; it is the remaining process step on this same
  ticket.
- PYPOST-1165 … PYPOST-1172 remain on PYPOST-1155; do not reparent.
- Remaining MCP-TM / WS-TM implementation work stays on those child
  stories, not on PYPOST-1174.

**Pre-existing test failures:** none — no test suite was run.

STEP 7 stays `[/]` in `00-roadmap.md` until the acceptance gate owner
marks `[x]`.
