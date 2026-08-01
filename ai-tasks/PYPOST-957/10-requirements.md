# PYPOST-957: Caplog proof for name=url_router in mapping GUI module

## Goals

[PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870) added pure-unit
caplog proofs for HTTP stub install events, including `name=url_router` when
a Mapping is installed. [PYPOST-904](https://pypost.atlassian.net/browse/PYPOST-904)
extended that pattern to the live GUI Send path for single-canned
`seed_get_ok` installs in the env module.

[PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) introduced a
mapping multi-URL GUI Send scenario under one Mapping stub, but did not add a
GUI-path caplog re-assert for the `url_router` install name. Maintainers
therefore rely on unit matrix coverage alone for Mapping installs on the real
UI → Send path.

**Business why:** Close optional low-priority testing debt so Mapping stub
install logging is proven once on the live agent e2e GUI path — sibling
confidence to PYPOST-870 / PYPOST-904 without changing product behavior.

Source: [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901)
`60-tech-debt.md` TD-3 → [PYPOST-957](https://pypost.atlassian.net/browse/PYPOST-957).

## Programming Language

Python 3.10+ for the agent e2e GUI caplog smoke. Developer docs in English
Markdown.

## User Stories

- As a **maintainer**, I want a marked `agent_e2e` caplog smoke in the mapping
  multi-URL GUI module that asserts `agent_e2e_http_stub_installed
  name=url_router`, so Mapping install logging is verified on the live Send
  path — not only in unit caplog matrix tests.
- As a **scenario author**, I want a discoverable example mirroring the env
  GET install-log smoke (PYPOST-904) but for Mapping stubs, so I can copy the
  caplog pattern for multi-URL scenarios.
- As a **CI runner**, I want the proof to stay bounded and deterministic under
  `make test-agent-e2e` with no live external HTTP.

## Definition of Done

- A caplog assertion in `tests/test_agent_e2e_http_mapping_multi_url.py` covers
  `agent_e2e_http_stub_installed name=url_router` during a live Mapping GUI
  Send (stub CM enter + UI click + settle under caplog).
- The test uses the same logger scope and pattern as sibling GUI install-log
  smokes (`pypost.fixtures.agent_e2e_http`, INFO).
- Full mapping module green under `make test-agent-e2e`.
- No intentional product UX or logging behavior change.
- Steps 1–8 artifacts exist under `ai-tasks/PYPOST-957/`.

Acceptance (from Jira): **Caplog assertion covers url_router install name in
mapping GUI path.**

## Task Description

**Problem:** Unit caplog matrix (PYPOST-870 / 903) and env GUI smoke (904)
prove install logging for catalog entries and `url_router` at the stub
boundary. The mapping multi-URL GUI module (901) exercises Mapping installs on
the real Send path but lacks a caplog re-assert for `name=url_router`.

**Business need:** Optional sibling debt — low signal once unit + install log
contract exist, but closes the GUI-path gap for Mapping installs.

### In Scope

- One thin `agent_e2e` caplog smoke in the existing mapping multi-URL module.
- Minimal GET Send under a one-entry Mapping stub suffices (install log fires
  on CM enter).
- Developer-doc mention alongside existing caplog matrix / env smoke notes.
- Steps 1–8 workflow artifacts.

### Out of Scope

- Changing Mapping router implementation or install log format.
- Full caplog matrix expansion (owned by PYPOST-903).
- Migrating other scenarios to Mapping stubs.
- User-facing product docs (`doc/user/`).
- Jira Debt ticket creation from Step 7 (orchestrator handles follow-ups).

## Functional Requirements

- FR1: Caplog smoke wraps Mapping stub install + GUI Send + settle at INFO on
  `pypost.fixtures.agent_e2e_http`.
- FR2: Assert includes `agent_e2e_http_stub_installed name=url_router`.
- FR3: Uses `agent_e2e_http_stub` with a Mapping argument (not single canned).
- FR4: Module retains explicit timeout markers per project testing rules.
- FR5: Existing happy-path and timeout-companion tests remain green.

## Non-Functional Requirements

- **Minimalism:** One thin smoke; not a duplicate of unit matrix.
- **Boundedness:** Same 60 s module timeout and settle budget as siblings.
- **Consistency:** Mirror PYPOST-904 env caplog pattern.
- **No product impact:** Test harness / docs hygiene only.

## Constraints and Assumptions

- Parent debt: [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) TD-3.
- Mapping install already logs `name=url_router` by default (868); this task
  adds GUI-path proof only.
- Blank session + explicit fill acceptable (same as mapping happy path).
- Priority: Low. Labels: `agent`, `e2e`, `tech-debt`, `testing`.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Mapping stub | Routes Send by URL; install name defaults to `url_router` |
| Caplog smoke | Captures install log during live GUI Send |
| Maintainer | Runs `make test-agent-e2e` on mapping module |

## Q&A

| Q | A |
| --- | --- |
| Why add GUI caplog if unit matrix covers url_router? | PYPOST-904 established GUI-path install-log smoke precedent; Mapping module was the remaining gap (901 TD-3). |
| Must the smoke Send twice? | No — install log fires on stub enter; one GET Send is enough. |
| Product impact? | None — test / docs only. |
