# PYPOST-959: HTTP method case normalization in URL router

## Goals

[PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902) shipped compound
`"{METHOD} {URL}"` keys on the agent e2e Mapping URL router. Lookup used the
request method string as-is, so a map keyed with `GET https://…` missed when
the UI or worker sent `get`, `Get`, or other mixed casing.

**Business why:** Lower friction for scenario authors when request method
casing is inconsistent across layers — normalize at the stub boundary only.

Source: [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902)
`60-tech-debt.md` → [PYPOST-959](https://pypost.atlassian.net/browse/PYPOST-959).

## Programming Language

Python 3.10+ for the fixture helper and unit proofs. Developer docs in English
Markdown.

## User Stories

- As a **scenario author**, I want compound map keys with uppercase methods
  (e.g. `GET https://…`) to match regardless of request method casing, so I
  do not need to mirror inconsistent casing from the UI.
- As a **maintainer**, I want documented normalization rules so authors know
  map keys should use uppercase HTTP methods.
- As a **pack owner**, I want existing compound-key and bare-URL proofs from
  PYPOST-902 / PYPOST-958 to remain green.

## Definition of Done

- `_resolve_url_router_response` uppercases the request method when building
  the compound lookup key.
- Unit test proves mixed-case request method matches uppercase compound map key.
- Developer docs updated in `doc/dev/agent_e2e_http.md`.
- Steps 1–8 artifacts exist under `ai-tasks/PYPOST-959/`.
- No intentional product UX or live-network behavior change.

Acceptance (from Jira): **Mixed-case method lookup works; docs updated.**

## Task Description

**Problem:** Compound key lookup uses `f"{method} {url}"` verbatim. Mixed-case
request methods miss uppercase map keys.

**Business need:** Optional debt closure from PYPOST-902 — tolerate inconsistent
HTTP method casing at the stub router only.

### In Scope

- Uppercase request `method` before compound key lookup.
- Unit proof for mixed-case request against uppercase map key.
- Developer-doc note on method normalization and uppercase map-key convention.
- Workflow artifacts Steps 1–8.

### Out of Scope

- Normalizing map key strings at author write time (convention: uppercase).
- Case-folding bare URL keys.
- GUI scenario dedicated to mixed-case methods (unit proof sufficient).
- Product runtime HTTP client changes.

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Compound lookup uppercases request method before key match. |
| FR2 | Bare URL fallback unchanged (exact URL string equality). |
| FR3 | Existing uppercase-method compound proofs remain green. |
| FR4 | Mixed-case request method matches uppercase compound map key. |
| FR5 | Match rules documented for authors. |

## Non-Functional Requirements

- Test-only / fixture-layer change; no product runtime change.
- Per-test timeout markers on new/changed tests (module `pytestmark`).

## Open Questions / Decisions

| Question | Decision |
| --- | --- |
| Normalize request or map keys? | Request method only — map keys stay uppercase per 902 docs. |
| Which case rule? | `str.upper()` on HTTP method token (GET, POST, …). |
| Why no GUI scenario? | Stub-boundary concern; unit proof matches 902/958 pattern. |
