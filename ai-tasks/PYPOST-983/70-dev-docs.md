# PYPOST-983: Developer Documentation Update

## Decision

**Update required and completed.** The task centralizes the existing
`FORCED_SETTLE_TIMEOUT_S = 0.05` value for three asynchronous UI test
companions. While application behavior, test selection, timeout semantics,
diagnostics, and normal settle budgets are unchanged, the existing developer
guidance contained a stale ownership statement for this concrete test
contract. The mapping timeout companion is now documented as receiving
`FORCED_SETTLE_TIMEOUT_S` from the shared test helper
`tests.helpers.agent_e2e_timeouts`, preserving the 0.05-second policy and
making the ownership discoverable to maintainers.

The new `tests/helpers/agent_e2e_timeouts.py` module is self-documenting: its
module docstring identifies the scope, its comment explains the near-zero
forced-timeout purpose, and its `__all__` exposes only the shared policy value.
The consumer imports also make the policy dependency visible at each use site.

## Repository Evidence

The following developer guidance was reviewed:

- `doc/dev/agent_e2e_http.md` was corrected in the mapping timeout companion
  table: `FORCED_SETTLE_TIMEOUT_S` is provided by
  `tests.helpers.agent_e2e_timeouts`, not module-local, while its 0.05-second
  policy remains unchanged.
- `doc/dev/agent_golden_e2e.md` describes the forced-timeout companion as a
  separate diagnostic path from successful settling, including its impossible
  status, 50 ms budget, and preserved response evidence. The implementation
  changes only where that value is owned.
- `doc/dev/testing.md` requires every collected test to declare an explicit
  timeout. The affected modules retain their existing module-level
  `pytest.mark.timeout(60)` declarations, and no timeout rule changed.
- `doc/dev/agent_e2e.md` remains the accurate umbrella guide for the agent e2e
  harness and its existing wait, lifecycle, and scenario documentation. The
  shared scalar does not add a public harness API or configuration setting.

No additional developer documentation page is needed; the targeted correction
updates the existing test-harness guidance without duplicating it or changing
behavior developers need to use differently.

## Scope Reviewed

- `ai-tasks/PYPOST-983/10-requirements.md`
- `ai-tasks/PYPOST-983/20-architecture.md`
- `ai-tasks/PYPOST-983/40-code-cleanup.md`
- `ai-tasks/PYPOST-983/50-observability.md`
- `ai-tasks/PYPOST-983/60-tech-debt.md`
- `tests/helpers/agent_e2e_timeouts.py`
- The golden, dialog, and mapping companion import/use changes

- `doc/dev/agent_e2e_http.md` — corrected the stale helper-ownership statement

No source, test logic, protected baseline, `AGENTS.md`, sprint registry, or
unrelated file was changed by Step 8. The Step 8 artifact is accepted, and the
task is at final commit-gate review.

## Validation

- `make lint` — passed
- `make verify-ai-tasks` — passed
