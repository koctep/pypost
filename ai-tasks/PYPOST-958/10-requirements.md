# PYPOST-958: GUI scenario same-URL GET+POST compound-key map

## Goals

[PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902) extended the
Mapping URL router with compound `"{METHOD} {URL}"` keys and shipped unit
proofs for same-URL multi-method routing. That delivery intentionally
deferred a GUI scenario — unit proofs satisfied acceptance.

**Business why:** Optional low-priority confidence raise — prove the compound-key
Mapping path on the live agent e2e Send → panel stack, sibling to
PYPOST-901’s distinct-URL GUI scenario, without changing product behavior.

Source: [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902)
`60-tech-debt.md` → [PYPOST-958](https://pypost.atlassian.net/browse/PYPOST-958).

## Programming Language

Python 3.10+ for the agent e2e GUI scenario. Developer docs in English
Markdown.

## User Stories

- As a **scenario author**, I want a marked `agent_e2e` example that Sends GET
  and POST to the same resolved URL under compound-key Mapping entries, so I
  can copy the pattern without writing a custom callable router.
- As a **maintainer**, I want panel outcome asserts on both Sends, so
  compound-key routing is proven on the real UI → worker → stub boundary.
- As a **CI runner**, I want the scenario bounded and deterministic under
  `make test-agent-e2e` with no live external HTTP.

## Definition of Done

- A marked `agent_e2e` GUI module drives GET then POST to one resolved URL
  under compound keys (`GET {url}` / `POST {url}`) inside one Mapping stub
  scope and asserts distinct panel bodies.
- Inventory gate in `tests/test_agent_e2e_http.py` locks the scenario callable.
- Module green under `make test-agent-e2e`.
- Harness table and HTTP fixture docs updated for discoverability.
- No intentional product UX or runtime change.
- Steps 1–8 artifacts exist under `ai-tasks/PYPOST-958/`.

Acceptance (from Jira): **Marked GUI scenario proves compound-key multi-method
Send path.**

## Task Description

**Problem:** PYPOST-902 unit proofs call `send_request` directly; no GUI
scenario exercises compound keys on the live Send path.

**Business need:** Close optional debt from PYPOST-902 follow-up row — GUI
smoke for same-URL GET+POST under compound keys.

### In Scope

- New `agent_e2e` GUI module (sibling to mapping multi-URL 901).
- Blank session + explicit fill; one Mapping stub; two Sends; panel asserts.
- Inventory gate + developer-doc discoverability.
- Steps 1–8 workflow artifacts.

### Out of Scope

- Changing Mapping router implementation (902 owns lookup).
- Timeout companion or caplog smoke (955 / 957 cover mapping module family).
- Method case normalization (PYPOST-959).
- User-facing product docs (`doc/user/`).

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Map uses compound keys for GET and POST on the same resolved URL. |
| FR2 | Both Sends run inside one `agent_e2e_http_stub(responses_map)` scope. |
| FR3 | Panel asserts distinct GET and POST canned bodies after settle. |
| FR4 | Module carries explicit timeout markers per project testing rules. |
| FR5 | Inventory gate asserts scenario callable exists. |

## Non-Functional Requirements

- **Minimalism:** One happy-path scenario; no duplicate of unit proofs.
- **Boundedness:** 60 s module timeout; shared 15 s settle budget.
- **Consistency:** Mirror PYPOST-901 blank-session + fill boundary.
- **No product impact:** Test harness / docs only.

## Constraints and Assumptions

- Parent: [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902).
- Compound router already shipped; this task adds GUI proof only.
- Shared URL may reuse seed GET resolved URL constant; POST canned result
  must use the same URL in `make_canned_http_result`.
- Priority: Lowest. Labels: `agent`, `e2e`, `tech-debt`, `testing`.

## Q&A

| Q | A |
| --- | --- |
| Why a new module vs extend multi-URL 901? | Distinct scenario shape (same URL + compound keys); keeps 901 focused on distinct URLs. |
| Unit proofs enough? | Yes for 902 AC; 958 is optional confidence only. |
| Product impact? | None — test / docs only. |
