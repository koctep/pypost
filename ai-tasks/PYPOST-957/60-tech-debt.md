# PYPOST-957: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: caplog smoke in
`tests/test_agent_e2e_http_mapping_multi_url.py` asserts
`agent_e2e_http_stub_installed name=url_router` during live Mapping GUI Send
(stub CM + click + settle). Module green under `make test-agent-e2e` (3
tests). Explicit timeout markers present. No product runtime change.

## Shortcuts Taken

- **One GET Send only.** Install log fires on stub CM enter; two Sends not
  required for caplog proof (same thin-smoke pattern as PYPOST-904 env module).
- **Blank session + explicit fill.** Matches mapping happy-path boundary.
- **No inventory gate.** PYPOST-904 precedent — direct caplog smoke in target
  module; infrastructure already green.

## Code Quality Issues

None material. Constants and caplog shape mirror env GET smoke (904).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Mapping GUI caplog `name=url_router` | **Covered** (957) |
| Unit matrix `url_router` | Covered (870 / 903) |
| Env GUI caplog `seed_get_ok` | Covered (904) |
| POST Send caplog in mapping module | Not duplicated — install name same on enter |

No timeout-marker blockers.

## Performance Concerns

None. One additional bounded Send settle in mapping module; typical run
unchanged materially.

## Deviations from Architecture

None.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent mapping GUI scenario | [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) |
| Unit caplog matrix | [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) / [903](https://pypost.atlassian.net/browse/PYPOST-903) |
| Env GUI install caplog | [PYPOST-904](https://pypost.atlassian.net/browse/PYPOST-904) |
| Mapping timeout companion | [PYPOST-955](https://pypost.atlassian.net/browse/PYPOST-955) |
| Shared settle helper | [PYPOST-956](https://pypost.atlassian.net/browse/PYPOST-956) |

### NON-BLOCKER

None — this task closed the optional TD-3 debt from PYPOST-901.

### Accepted / out of scope (do not ticket)

- Parametrized GUI caplog matrix for all install names — PYPOST-903 scope.
- Second Send in caplog smoke — install log already captured on enter.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — Mapping GUI path caplog proof for `name=url_router` is in
place. No unticketed NON-BLOCKER debt remains for this task.
