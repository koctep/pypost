# PYPOST-948: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Sibling agent e2e Send settle now uses identity-scoped text waits via shared
`wait_response_after_send`; mandatory modules guarded by convention lock;
optional seed POST migrated; `make test-agent-e2e` green. Test-only scope held.
Items below are non-blocking.
**Do not create Jira tickets in this step** — link existing follow-ups where
tracked; unticketed items listed for orchestrator Phase D.

## Shortcuts Taken

- **Seed POST tree Send uses helper `in_current_tab=True` workaround** instead
  of session-level tab-scoped text waits. Matches requirements until
  [PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949).
- **Seed POST not in convention lock list.** Mandatory three modules are
  AST-guarded; seed POST was optional scope but was migrated — no structural
  guard yet.
- **Golden e2e unchanged.** Still uses inline tab-scoped `wait_for_text`; does
  not adopt `wait_response_after_send` (architecture out of scope).
- **Post-settle asserts still use compact `_BODY_IN_SNAPSHOT` in joined checks**
  where snapshot sanitize carries compact JSON — intentional; only readiness
  waits use display form.
- **Full `make check` not re-run.** Step 5 validated lint + scoped flake8 +
  `make test-agent-e2e` (83 passed). Step 8 dev docs complete.

## Code Quality Issues

- None that block close. Implementation matches architecture: shared helper,
  display-form JSON via `json_response_body_display`, post-settle snapshot
  cardinality unchanged.

| Architecture | Implementation | Assessment |
| --- | --- | --- |
| Status then body text wait on catalog ids | `wait_response_after_send` | Match |
| Display-form JSON body waits | `_BODY_DISPLAY` / helper | Match |
| Post-settle snapshot cardinality | Unchanged | Match |
| Chunk-flush delay retained | double-body / matrix | Match |
| Seed POST tree-open snapshot wait | `_seed_post_editor_ready` kept | Match |
| Convention lock on mandatory siblings | 3 modules in `_SEND_SETTLE_MODULES` | Match |

## Missing Tests

| Scenario | Status |
| --- | --- |
| Mandatory siblings use text-wait settle (no `_response_ready`) | Covered (convention) |
| Double-body green + red path | Covered (agent e2e) |
| Presentation matrix smoke cells | Covered (agent e2e) |
| Env Send + caplog stub installed | Covered (agent e2e) |
| Seed POST blank + tree-open Send | Covered (agent e2e) |
| Full matrix cartesian (`slow`) | Not re-run (smoke only) |
| Convention guard for seed POST module | Not covered — optional follow-up |
| Golden adopts shared settle helper | Out of scope |
| Forced timeout on text-wait settle path (golden lock) | Not covered — PYPOST-950 |

**No timeout-marker blockers.** All changed modules declare `pytestmark =
timeout(60)`.

## Performance Concerns

None material. Send settle polls named status/body widgets instead of
full-panel snapshot walks — modest improvement on hot path. Post-settle
snapshot walks unchanged.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Tab-scoped `AgentAppSession.wait_for_text` (or root override) | Seed POST tree path uses helper `in_current_tab=True`; session API still window-rooted for free-function callers | [PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949) |
| TD-2 | Low | Align golden timeout-diagnostics lock with text-wait settle | Force `wait_for_text` miss while keeping `step` + `response_excerpt` wrapping | [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950) |
| TD-3 | Low | Extend Send settle convention lock to seed POST | Optional module migrated but not in `_SEND_SETTLE_MODULES` | [PYPOST-969](https://pypost.atlassian.net/browse/PYPOST-969) |
| TD-4 | Low | Golden adopt `wait_response_after_send` for DRY settle | Reduces duplicate timeout wrap; golden tab-scoped root differs today | [PYPOST-970](https://pypost.atlassian.net/browse/PYPOST-970) |
| TD-5 | Low | Step 8 dev docs — sibling text-wait settle | **Done** — `doc/dev/agent_e2e_send_settle.md` + related updates | Step 8 artifact |

### Resolved by this ticket

| Prior debt | Resolution |
| --- | --- |
| [PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920) TD-1 sibling panel-walk settle | Completed in PYPOST-948 |

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | `in_current_tab` on helper only — tracked as PYPOST-949 |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — test-only, helper + rewires as planned |
| Hardcoded values | Uses shared `SEND_SETTLE_TIMEOUT_S` from send helper |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — Definition of Done satisfied: mandatory siblings + env on
text-wait settle, optional seed POST migrated, suite green, convention lock
green. Remaining gaps are non-blocking follow-ups (PYPOST-949/950 and optional
hygiene).

## Worklog

```
tokens_used: 42000
role: execution
step: 7
step_name: Review
```
