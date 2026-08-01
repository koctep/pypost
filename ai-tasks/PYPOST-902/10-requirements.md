# PYPOST-902: Optional method+URL compound map keys

## Goals

[PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868) shipped a URL→canned
Mapping router on the shared agent e2e HTTP stub layer using **exact URL keys
only**. When two HTTP methods share one resolved URL in a scenario, authors
must fall back to a custom callable `side_effect` instead of a simple map.

This optional debt extends the router so authors may key entries as
`"{METHOD} {URL}"` (e.g. `GET https://example.test/shared`) while keeping
bare URL keys working for existing scenarios.

Source: [PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868) tech debt
→ [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902).

## Programming Language

Python 3.10+ for the fixture helper and unit proofs. Developer docs in English
Markdown.

## User Stories

- As a **scenario author**, I want Mapping stub keys that combine method and
  URL, so I can route GET and POST to the same resolved URL without writing a
  custom callable.
- As a **maintainer**, I want documented match precedence between compound
  and bare URL keys so authors know which entry wins when both exist.
- As a **pack owner**, I want existing bare-URL maps and unit/GUI proofs from
  PYPOST-868 / PYPOST-901 to remain green — additive match rules only.

## Definition of Done

- `url_router_side_effect` (and therefore `stub_agent_e2e_http(Mapping)`) accepts
  compound keys `"{METHOD} {URL}"` in addition to bare URL keys.
- Match precedence is documented: compound key first, then bare URL fallback.
- Unit tests prove: same URL / different methods via compound keys; bare URL
  backward compatibility; compound-over-bare precedence when both exist; miss
  still raises `AssertionError` listing known keys.
- Developer docs updated in `doc/dev/agent_e2e_http.md`.
- Steps 1–8 artifacts exist under `ai-tasks/PYPOST-902/`.
- No intentional product UX or live-network behavior change.

Acceptance (from Jira): **Extend match rules (e.g. `GET https://…` keys) and
document precedence vs bare URL keys.**

## Task Description

**Problem:** v1 URL router matches `request_data.url` to map keys exactly. Two
methods on one URL require a callable router.

**Business need:** Lower friction for multi-method / same-URL agent e2e scenarios
while preserving v1 maps.

### In Scope

- Compound key format: `"{request_data.method} {request_data.url}"` (single
  ASCII space separator; method and URL taken as-is from the request object).
- Lookup order: try compound key, then bare URL key.
- Unit proofs and developer-doc match-rule update.
- Workflow artifacts Steps 1–8.

### Out of Scope

- Glob/prefix URL match, ordered multi-call queues, method-only keys.
- GUI scenario dedicated to compound keys (unit proofs sufficient).
- Normalizing HTTP method casing beyond what the request object carries.

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Mapping router resolves compound key `"{method} {url}"` when present. |
| FR2 | When compound key misses, router falls back to bare `url` key (v1 compat). |
| FR3 | When both compound and bare keys exist, compound match wins for that method. |
| FR4 | Unknown request still raises `AssertionError` with `url=` and sorted known keys. |
| FR5 | Existing bare-URL unit and GUI proofs remain green. |
| FR6 | Match precedence documented for authors. |

## Non-Functional Requirements

- Test-only / fixture-layer change; no product runtime change.
- Per-test timeout markers on new/changed tests (`pytestmark` or function mark).

## Open Questions / Decisions

| Question | Decision |
| --- | --- |
| Key format? | `"{METHOD} {URL}"` — matches Jira example and PYPOST-868 debt note. |
| Precedence? | Compound before bare URL; bare URL serves v1 maps and method-agnostic entries. |
| Why no GUI scenario? | Same-URL multi-method is stub-boundary concern; unit proofs match 868/901 pattern. |
