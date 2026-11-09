# PYPOST-1535: Technical Debt Analysis

## Shortcuts Taken

None. The fix is the minimal correct product change: keep atomic `tools_map`
assignment, drop the redundant deep copy introduced with PYPOST-1465.

## Code Quality Issues

- PYPOST-1465 architecture text still says `register_tools` builds a map of
  “RequestModel copies”; runtime behavior now preserves identity. Dev docs were
  updated in this task; older `ai-tasks/PYPOST-1465/*` artifacts remain
  historical and were not rewritten.

## Missing Tests

- Existing four identity `assertIs` cases cover the regression. No additional
  dedicated repro file was added (2 SP debt; existing reds were sufficient).

## Performance Concerns

- Removing an extra deep copy per registered tool slightly reduces register/
  refresh cost. Negligible for typical collection sizes.

## Follow-up Tasks

| Item | Verdict | Notes |
| --- | --- | --- |
| Unrelated suite failures (e.g. LOC inventory / solid-audit snapshot drift seen in full `make test`) | NON-BLOCKER — pre-existing / out of scope | Do not fix inside PYPOST-1535 |
| Historical PYPOST-1465 ai-task wording about “copies” in `register_tools` | NON-BLOCKER — docs drift in closed task folder | Prefer current `doc/dev/mcp_process_isolation.md` |
