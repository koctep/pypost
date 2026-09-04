# PYPOST-983: Technical Debt Analysis

## Scope

This review covers only debt introduced or exposed by centralizing
`FORCED_SETTLE_TIMEOUT_S` for the golden, dialog, and mapping forced-settle
companions. The implementation is test-only and keeps the existing 0.05-second
value, wait mechanisms, diagnostics, assertions, and normal settle budgets.

## Debt Decision

No actionable technical debt was introduced or exposed by this change. The
shared module has one narrowly scoped value, the three consumers have explicit
direct imports, and the scenario-specific responsibilities remain in their
existing modules. The observations below are informational maintenance triggers,
not follow-up work required for PYPOST-983.

## Shortcuts Taken

None. The change uses a dedicated policy module rather than placing the forced
budget in a scenario-specific helper or changing any wait abstraction. No
production behavior, timeout policy, or unrelated test helper was refactored.

## Code Quality Issues

No actionable issue was found.

### Informational observations and future triggers

- **Helper ownership:** `tests/helpers/agent_e2e_timeouts.py` intentionally
  exports only the shared constant. If it begins to contain wait logic,
  diagnostics, or multiple unrelated policies, split those responsibilities
  before adding more consumers.
- **Import coupling:** Direct imports make each dependency visible at its use
  site and avoid coupling consumers to a package re-export. If the helper is
  consumed broadly outside agent e2e tests, reassess its package boundary and
  whether a more explicit policy API is warranted.
- **Duplicated scenario setup:** Golden, dialog, and mapping setup remains
  separate because their wait primitives and diagnostics differ. If two flows
  acquire identical setup, cleanup, and assertion behavior, consider a focused
  scenario helper rather than expanding the timeout module.

## Missing Tests

No task-scoped coverage gap was found. The existing three companion paths still
exercise the shared value through their original waits, and their module-level
60-second timeout markers remain in place. If the policy module gains behavior
or validation logic beyond a constant, add a direct contract test for that
behavior and keep the companion tests as integration coverage.

## Performance Concerns

No performance concern was introduced. The helper is imported once per test
module and supplies an immutable scalar; forced waits retain the existing
bounded 0.05-second budget and normal asynchronous settle waits retain their
independent budgets.

## Timeout Policy Boundaries

The forced-settle policy remains distinct from `SEND_SETTLE_TIMEOUT_S` and the
dialog normal-settle budget. This separation prevents a maintenance change to
failure probes from weakening happy-path waits. Treat any future call site that
uses the forced constant for a normal settle, or introduces another near-zero
forced value, as a trigger for a policy review and consumer audit.

## Validation Maintenance

The current validation contract is sufficient for this value-only change:
focused companion tests, `make lint`, and `make verify-ai-tasks`. If additional
forced-settle consumers are added, extend the focused coverage and audit for
duplicate literals or local definitions before accepting the change.

## Follow-up Tasks

None required for PYPOST-983. The future triggers above should become a Jira
follow-up only when their stated evidence appears; no speculative issue is
created by this analysis.
