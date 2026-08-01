# PYPOST-960: Extract shared dump best-effort exception tuple

## Goals

PYPOST-914 duplicated the same best-effort exception tuple in lifecycle and
fixtures to avoid circular imports. Maintaining two copies risks drift when
members are updated. A single shared definition keeps dump-hook and dump-helper
behavior aligned without manual synchronization.

## User Stories

- As a maintainer, I want one canonical best-effort exception tuple for agent
  e2e failure dumps so lifecycle and fixtures cannot diverge silently.
- As a developer debugging e2e failures, I want unchanged catch semantics so
  existing WARNING logs and propagation rules still apply.

## Definition of Done

- One shared tuple lives in a neutral module under `pypost/agent/`.
- `lifecycle.py` and `fixtures/agent_e2e_failure.py` import that tuple; local
  duplicate definitions are removed.
- Existing agent e2e failure artifact tests pass with no behavior change.
- Developer docs reference the shared module instead of per-file private tuples.

## Task Description

Follow-up from [PYPOST-914](https://pypost.atlassian.net/browse/PYPOST-914)
tech debt. Move `_DUMP_BEST_EFFORT_ERRORS` / `_DUMP_HOOK_BEST_EFFORT_ERRORS` to
`pypost/agent/e2e_dump_errors.py` so both call sites share one definition
without circular imports (fixtures may still import `AgentAppSession` from
lifecycle; the shared module must not import lifecycle or fixtures).

## Q&A

- **Why not import from fixtures in lifecycle?** Fixtures depend on lifecycle;
  importing fixtures from lifecycle would create a circular import.
- **Behavior change?** No — same exception types, same catch/propagate rules.
