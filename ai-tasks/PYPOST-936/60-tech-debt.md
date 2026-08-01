# PYPOST-936: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: shared helper `tests/helpers/agent_e2e_dialog_settle.py` with
`run_product_dialog_settle` used by both product-dialog settle proofs; convention
test locks adoption; no production API changes. Module green under
`make test-agent-e2e` (2 tests, ~0.8 s). Closes
[PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) TD-3.

## Shortcuts Taken

- **Settings predicate stays test-local.** `_settings_dialog_present()` remains in
  the test module — only timer/rewrap/dismiss orchestration is shared.
- **Convention test uses source scan.** Structural lock (import + call count), not
  AST — sufficient for one module with two proofs; matches PYPOST-948 posture.
- **Helper returns `(settled_ok, errors)` tuple.** Async timer callback cannot use
  outer `pytest.raises`; same `settle_error` pattern as before, now inside helper.

## Code Quality Issues

None blocking. Helper mirrors `agent_e2e_send_settle.py` structure.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Happy-path via shared helper | Covered |
| Timeout companion via shared helper | Covered |
| Convention lock on helper import | Covered |
| Third dialog scenario | Out of scope until needed |
| Explicit timeout markers | Present — module `pytestmark` includes `timeout(60)` |

## Performance Concerns

None. Same bounded waits; no new production overhead.

## Deviations from Architecture

None material.

## Follow-up Tasks

### Closed by this story

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-3 | Low | Shared modal settle helper for agent e2e | **Done** — `agent_e2e_dialog_settle.py` |
| | | | Source: [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) TD-3 |

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| `SETTINGS_DIALOG` widget identity | [PYPOST-935](https://pypost.atlassian.net/browse/PYPOST-935) |
| Dialog settle timeout `caplog` polish | [PYPOST-968](https://pypost.atlassian.net/browse/PYPOST-968) |
| Qt/PySide segfault infrastructure | [PYPOST-429](https://pypost.atlassian.net/browse/PYPOST-429) lineage |

### NON-BLOCKER

None — no new unticketed debt.

### Accepted / out of scope (do not ticket)

- Migrate `SettingsDialog` from `exec()` to `open()` — product change.
- Full product dialog matrix — requirements out of scope.
- Golden Send helper changes — separate surface (PYPOST-948).

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | Timer-before-exec required; now centralized in helper |
| Missing tests with timeout markers | None |
| Deviations from architecture | None |
| Production API changes | None |
| Merge / release blocker debt | None |

**SAFE TO CLOSE** — PYPOST-919 TD-3 satisfied; remaining siblings are identity
hygiene (PYPOST-935) and optional caplog polish (PYPOST-968).
