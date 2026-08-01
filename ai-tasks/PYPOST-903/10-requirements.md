# PYPOST-903: Optional caplog matrix for stub install name tokens

## Goals

[PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) added a caplog proof
that the shared agent e2e HTTP stub emits `agent_e2e_http_stub_installed` with
`name=golden_ok` when installing the golden catalog constant. Production already
maps other catalog constants, URL-router Mapping installs, and explicit custom
`name=` overrides to distinct `name=` tokens — but only `golden_ok` is asserted
in tests today.

This optional debt widens the caplog matrix so catalog rename or logging regressions
are caught beyond the single golden case.

Source: [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) tech debt
→ [PYPOST-903](https://pypost.atlassian.net/browse/PYPOST-903).

## Programming Language

Python 3.10+ for pytest caplog proofs. Developer docs in English Markdown.

## User Stories

- As a **maintainer**, I want caplog proofs for each catalog install name token
  (`seed_get_ok`, `seed_post_ok`, `double_body_lock_ok`), so catalog identity
  renames do not silently break logging contracts.
- As a **maintainer**, I want caplog proof for Mapping installs (`url_router`) and
  an explicit custom `name=` override, so router and author naming paths stay
  greppable in CI.
- As a **pack owner**, I want the proofs to stay in the dedicated pure-unit stub-logs
  module (mirroring PYPOST-870 / PYPOST-867) without pulling in live GUI sessions.

## Definition of Done

- Parametrized or table-driven caplog asserts cover install name tokens beyond
  `golden_ok`: catalog constants, `url_router`, and at least one explicit custom
  `name=`.
- Existing golden proof remains green; no production behavior change.
- Steps 1–8 artifacts exist under `ai-tasks/PYPOST-903/`.
- Developer docs note the expanded caplog matrix.

Acceptance (from Jira): **Parametrized or table-driven asserts covering additional
install name tokens beyond golden_ok.**

## Task Description

**Problem:** HTTP stub install logging is verified for `golden_ok` only. Other
documented `name=` tokens rely on production code and docs without automated
caplog regression checks.

**Business need:** Broader logging-catalog proofs at low cost — pure unit, no GUI.

### In Scope

- Table-driven / parametrized caplog tests in `tests/test_agent_e2e_http_stub_logs.py`.
- Tokens: `seed_get_ok`, `seed_post_ok`, `double_body_lock_ok`, `url_router`,
  explicit custom `name=`.
- Workflow artifacts Steps 1–8.

### Out of Scope

- Live GUI re-assert of install events (unit path sufficient).
- New production logging events or metrics.
- Caplog proofs in behavioral stub modules (`tests/test_agent_e2e_http.py`).

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Caplog asserts `agent_e2e_http_stub_installed name=seed_get_ok` for `CANNED_SEED_GET_OK`. |
| FR2 | Caplog asserts `name=seed_post_ok` for `CANNED_SEED_POST_OK`. |
| FR3 | Caplog asserts `name=double_body_lock_ok` for `CANNED_DOUBLE_BODY_LOCK_OK`. |
| FR4 | Caplog asserts `name=url_router` for a Mapping install (default router name). |
| FR5 | Caplog asserts a custom `name=` when caller passes explicit `name=` override. |
| FR6 | `golden_ok` case remains covered (parametrize or retained). |
| FR7 | Module stays pure unit: `timeout(10)`, no `agent_e2e` marker. |

## Non-Functional Requirements

- Test-only change; no product runtime change.
- Per-test timeout markers on the module (`pytestmark`).

## Open Questions / Decisions

| Question | Decision |
| --- | --- |
| Parametrize vs sibling tests? | Single parametrized table (DRY, one caplog pattern). |
| Custom name fixture? | Non-catalog `make_canned_http_result` + explicit `name="scenario_alpha"`. |
| url_router case? | `{GOLDEN_URL: CANNED_GOLDEN_OK}` Mapping with default `name="custom"`. |
