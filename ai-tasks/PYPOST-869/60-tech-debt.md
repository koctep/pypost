# PYPOST-869: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Shared response-panel helpers are extracted, four Send consumers rewired,
unit + smoke agent e2e green. No product runtime change. Items below are
non-blocking follow-ups (orchestrator Phase D: ticket if desired; this
run does not create Jira Debt issues).

## Shortcuts Taken

- Scenario-specific `_response_ready` / `_assert_response_ui` remain
  local (by design) — only walk / subtree / excerpt / join are shared.
- Env Send still omits `response_panel_excerpt` on wait timeout (pre-existing
  diagnostics shape); optional consistency follow-up below.
- Did not introduce a shared `_SEND_SETTLE_TIMEOUT_S` constant (parent
  859 debt already noted hardcoded 15s).

## Code Quality Issues

- None material in the new helper module.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Helper API + synthetic tree | Covered (unit) |
| No local `_walk_values` / `_subtree_by_name` in consumers | Covered (AST) |
| Golden / env / double-body / matrix smoke | Covered (agent e2e) |
| Full matrix cartesian (`slow`) | Not re-run here (smoke only) |
| Caplog for helper module | N/A (no logging) |

No timeout-marker blockers.

## Performance Concerns

None — same walk algorithm as prior local copies.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent HTTP stub layer | [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859) |
| This share (self) | [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869) |

### NON-BLOCKER — need NEW Jira Debt tickets (Phase D)

#### Shared Send settle timeout constant

- **Priority:** Low
- **Description:** Golden / env / double-body / matrix still each define
  `_SEND_SETTLE_TIMEOUT_S = 15.0`. Drift risk if settle policy changes.
- **Remediation:** Export a named constant from
  `tests/helpers/agent_e2e_response_panel.py` (or a tiny
  `agent_e2e_timeouts.py`) and import in Send modules.
- **Jira:** [PYPOST-895](https://pypost.atlassian.net/browse/PYPOST-895)

#### Env Send timeout diagnostics use shared excerpt

- **Priority:** Low
- **Description:** `test_agent_e2e_http_env.py` wait-timeout path does not
  attach `response_excerpt` via `response_panel_excerpt`, unlike golden /
  double-body / matrix.
- **Remediation:** Align timeout re-raise with
  `response_panel_excerpt(last)` + diagnostics key.
- **Jira:** [PYPOST-896](https://pypost.atlassian.net/browse/PYPOST-896)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None — helper module + rewires as planned |
| Hardcoded values | Settle 15s still local (optional follow-up) |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR6 satisfied by shared helpers, rewires, unit
proof, green Send smoke, and (Step 8) docs. Remaining gaps are optional
hygiene.
