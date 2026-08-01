# PYPOST-956: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Mapping multi-URL Send settle now uses shared `wait_response_after_snapshot`;
local `_wait_response` and companion inline rewrap removed; convention locks
green; scoped agent e2e mapping suite green. Test-only scope held. Items below
are non-blocking.
**Do not create Jira tickets in this step** — link existing follow-ups where
tracked; unticketed items listed for orchestrator Phase D.

## Shortcuts Taken

- **Rewrap bodies duplicated between text-wait and snapshot helpers.** Snapshot
  path copies rewrap shape from `wait_response_after_send` with a different
  message template (step in message). Optional private
  `_rewrap_send_settle_timeout` deferred until a third consumer needs it.
- **Golden e2e unchanged.** Still uses inline tab-scoped `wait_for_text`; does
  not adopt shared settle helpers (PYPOST-948 deferral).
- **Module-local `FORCED_SETTLE_TIMEOUT_S = 0.05`.** Same constant name and
  value as golden/dialog companions; not centralized.
- **Full `make test-agent-e2e` not re-run.** Step 4 validated scoped mapping
  module + convention locks per architecture verify commands.

## Code Quality Issues

- None that block close. Implementation matches architecture: shared snapshot
  helper with `(step)` in timeout message, mapping happy path + companion
  migrated, text-wait helper unchanged.

| Architecture | Implementation | Assessment |
| --- | --- | --- |
| Snapshot helper in `agent_e2e_send_settle.py` | `wait_response_after_snapshot` | Match |
| Message `{prefix} ({step}): {exc}; …` | Snapshot helper rewrap | Match |
| Text-wait message unchanged | `wait_response_after_send` | Match |
| Mapping happy path uses shared helper | Two Send calls migrated | Match |
| Companion uses helper + short timeout | `FORCED_SETTLE_TIMEOUT_S` | Match |
| Convention lock on mapping module | AST gate in response panel tests | Match |

## Missing Tests

| Scenario | Status |
| --- | --- |
| Mapping happy path two-URL Send | Covered (agent e2e) |
| Mapping GET forced-timeout companion | Covered (agent e2e) |
| Snapshot settle convention lock | Covered (unit AST) |
| Shared helper import gate | Covered (`test_shared_send_settle_exports_…`) |
| Full `make test-agent-e2e` suite | Not re-run (scoped verify only) |
| Golden adopts shared settle helper | Out of scope |
| Private rewrap dedup unit test | Not needed — behavioral lock via companions |

**No timeout-marker blockers.** Changed mapping module declares
`pytestmark = timeout(60)`.

## Performance Concerns

None material. Refactor only; snapshot settle hot path unchanged.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Golden adopt `wait_response_after_send` for DRY settle | Tab-scoped root differs today | [PYPOST-970](https://pypost.atlassian.net/browse/PYPOST-970) |
| TD-2 | Low | Align golden timeout-diagnostics lock with text-wait settle | Force text-wait miss with `step` + excerpt | [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950) |
| TD-3 | Low | Extract private `_rewrap_send_settle_timeout` if third consumer appears | Must preserve byte-identical message templates per path | [PYPOST-985](https://pypost.atlassian.net/browse/PYPOST-985) |
| TD-4 | Low | Centralize `FORCED_SETTLE_TIMEOUT_S` across companion modules | Golden / dialog / mapping share 0.05 s value | [PYPOST-983](https://pypost.atlassian.net/browse/PYPOST-983) |
| TD-5 | Low | Step 8 dev docs — snapshot Send settle | **Done** — `agent_e2e_send_settle.md` + `agent_e2e_http.md` | Step 8 artifact |

### Resolved by this ticket

| Prior debt | Resolution |
| --- | --- |
| [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) TD-2 shared Send settle rewrap | Completed in PYPOST-956 |
| [PYPOST-955](https://pypost.atlassian.net/browse/PYPOST-955) duplicated companion inline rewrap | Companion now calls shared helper |

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None — direct helper extraction |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — test-only, helper + migration as planned |
| Hardcoded values | Uses shared `SEND_SETTLE_TIMEOUT_S` default; mapping prefix module-local |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — Definition of Done satisfied: shared snapshot helper,
mapping migrated, convention locks green, scoped suite green. Remaining gaps
are non-blocking follow-ups (PYPOST-950/970 and optional hygiene).

## Worklog

```
tokens_used: 45000
role: execution
step: 7
step_name: Review
```
