# PYPOST-904: Optional GUI-path install-log smoke

## Goals

[PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) and
[PYPOST-903](https://pypost.atlassian.net/browse/PYPOST-903) verify that the
shared agent e2e HTTP stub emits `agent_e2e_http_stub_installed` via pure-unit
caplog proofs in `tests/test_agent_e2e_http_stub_logs.py`. Production already
logs the event when a marked GUI Send scenario installs the stub — but no
`agent_e2e` Send test asserts that install event under caplog on the live
offscreen path.

This optional debt adds a thin GUI-path re-assert so install logging is
exercised end-to-end (fixture → stub CM → Send) rather than unit-only CM enter.

Source: [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) tech debt
→ [PYPOST-904](https://pypost.atlassian.net/browse/PYPOST-904).

## Programming Language

Python 3.10+ for pytest caplog + offscreen Qt agent e2e. Developer docs in
English Markdown.

## User Stories

- As a **maintainer**, I want a marked `agent_e2e` Send scenario to assert
  `agent_e2e_http_stub_installed` under caplog, so install logging is verified
  on the GUI path — not only via unit-only stub CM enter.
- As a **pack owner**, I want the smoke to extend an existing Send scenario
  (seed GET env Send) rather than a large new module, keeping harness-table
  surface minimal.
- As a **desktop user** (indirect), I want no product UX change — only test
  coverage for existing observability.

## Definition of Done

- A marked `agent_e2e` Send scenario asserts `agent_e2e_http_stub_installed`
  under caplog during a real offscreen Send flow (acceptance from Jira).
- Caplog scoped to `pypost.fixtures.agent_e2e_http` at INFO.
- Module retains explicit timeout marker; no production behavior change.
- Steps 1–8 artifacts exist under `ai-tasks/PYPOST-904/`.
- Developer docs note the GUI-path install-log smoke.

Acceptance (from Jira): **Marked agent_e2e Send scenario asserts
agent_e2e_http_stub_installed under caplog without unit-only stub drive.**

## Task Description

**Problem:** HTTP stub install logging is verified in a pure-unit module
(PYPOST-870 / 903) but not re-asserted when a GUI Send scenario wraps
`agent_e2e_http_stub` and clicks Send.

**Business need:** Optional e2e confidence that install events still emit on
the live agent path at low cost (one thin smoke).

### In Scope

- Extend `tests/test_agent_e2e_http_env.py` (seed GET env Send) with caplog
  assert for `agent_e2e_http_stub_installed name=seed_get_ok`.
- Workflow artifacts Steps 1–8.
- Dev docs cross-link to GUI-path smoke.

### Out of Scope

- New production logging events or metrics.
- Duplicating the full PYPOST-903 name matrix on GUI paths.
- Caplog proofs in the pure-unit stub-logs module (already covered).

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Marked `agent_e2e` test drives live session + Send under shared HTTP stub. |
| FR2 | Caplog at INFO on `pypost.fixtures.agent_e2e_http` captures install event. |
| FR3 | Assert `agent_e2e_http_stub_installed name=seed_get_ok` in caplog text. |
| FR4 | Stub context wraps Send click (not unit-only CM enter without GUI). |
| FR5 | Module keeps `timeout(60)` and `agent_e2e` markers. |

## Non-Functional Requirements

- Test-only change; no product runtime change.
- Reuse existing env Send helpers (`_response_ready`, settle timeout).
- Follow PYPOST-899 live caplog + PYPOST-870/903 logger scoping patterns.
