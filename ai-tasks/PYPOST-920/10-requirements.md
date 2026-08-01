# PYPOST-920: Optional response status/body widget ids

## Goals

AI agents and golden/e2e harnesses must wait for HTTP response **status** and
**body** text on dedicated, stable UI identities — not by walking the whole
response panel snapshot and coupling assertions to snapshot sanitize form.

Today only the response panel root has a stable identity. Status and body
surfaces under it do not. Golden and related e2e flows therefore join panel
snapshot values and match against sanitized text shape (for example compact
JSON re-dump), which is fragile and blocks use of targeted text waits.

**Business why:** Agents need reliable, identity-scoped waits on status and
body so Send → response proofs stay stable without snapshot-sanitize coupling.

Source: [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853)
(noted again under [PYPOST-889](https://pypost.atlassian.net/browse/PYPOST-889)
tech debt). Browse:
[PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920).

## Programming Language

Python (`.cursor/lsr/do-python.md`). UI identity and agent/golden harness
coverage. Developer docs in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **AI agent / e2e author**, I want stable identities on the response
  status and response body surfaces so I can wait for expected text on those
  targets instead of scanning the whole panel snapshot.
- As a **golden-flow maintainer**, I want Send → response proofs to stop
  depending on snapshot sanitize shape for status/body readiness, so body
  pretty-print vs compact sanitize differences do not break waits.
- As a **maintainer**, I want the new identities listed in developer identity
  docs and covered by the identity spot-check so regressions are caught in CI.
- As a **sibling e2e owner** (locks that still walk the panel), I want optional
  status/body ids available so future waits can migrate without inventing a
  parallel naming scheme.

## Definition of Done

- Stable widget identities exist for the response **status** surface and the
  response **body** surface (canonical names from acceptance:
  `pypost_response_status`, `pypost_response_body`).
- Agents/harnesses can target those identities with text waits (the existing
  wait-for-text capability) after Send / response settle.
- Identity spot-check covers the new status and body identities.
- Developer docs for UI identity (and golden e2e guidance as needed) document
  the new identities and that status/body can be waited on by id.
- Existing panel-level identity remains valid; this story adds finer targets,
  it does not remove the panel root identity.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

Acceptance (from Jira): **Stable ids applied on response status/body surfaces;
docs + spot-check updated.**

## Task Description

**Problem:** Response status and body UI surfaces lack dedicated stable
identities. Golden and related agent e2e flows observe status/body by walking
values under the response panel snapshot and coupling expected text to
sanitize behaviour. Targeted text waits need a widget id per surface and
cannot be used cleanly today.

**Business need:** Optional but first-class status and body identities so
agents and golden flows can wait for status/body text by identity, reducing
fragility and decoupling readiness from snapshot sanitize form.

### In Scope

- Add stable identities for response status and response body surfaces
  (`pypost_response_status`, `pypost_response_body`).
- Update identity catalog / developer identity docs so the new ids are
  discoverable next to existing response-panel identity.
- Update identity spot-check so the new ids are asserted present.
- Golden / agent flows use identity-scoped text waits for status and body
  (via the new identities) instead of panel-snapshot sanitize coupling.
- Keep the existing response panel root identity.

### Out of Scope

- Redesigning settle/wait helpers or inventing a new wait API family.
- Changing HTTP stubbing, canned golden payloads, or request Send behaviour.
- Full migration of every sibling e2e that still walks the panel (optional
  adoption; this story unlocks the ids).
- Broader response UI redesign (search chrome, headers tab, etc.).
- User-facing product docs (`doc/user/`).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: Response status surface has a stable identity
  `pypost_response_status` (catalogued like other key controls).
- FR2: Response body surface has a stable identity `pypost_response_body`
  (catalogued like other key controls).
- FR3: Existing response panel root identity remains available and unchanged
  in meaning.
- FR4: After a response is shown, agents can wait for expected status text
  via the status identity (text wait), without requiring a full-panel
  snapshot walk.
- FR5: After a response is shown, agents can wait for expected body text via
  the body identity (text wait), without requiring sanitize-coupled panel
  snapshot matching for readiness.
- FR6: Identity spot-check asserts the new status and body identities are
  present on the product UI.
- FR7: Developer docs list the new identities and note that golden/agent
  flows may wait on status/body by id (vs panel snapshot walk).

## Non-Functional Requirements

- **Stability:** Identities are English `pypost_`-prefixed snake_case and do
  not depend on localized display labels or theme cosmetics.
- **CI suitability:** Spot-check and any updated golden/agent coverage run
  under the project’s offscreen / standard test paths with bounded timeouts.
- **Compatibility:** Composes with existing lifecycle ready, actions, waits,
  and panel identity; does not break current panel-based proofs until they
  opt in.
- **Discoverability:** Maintainers find the new ids in identity docs without
  reverse-engineering UI code alone.
- **No production → tests imports:** Production code must not import from
  `tests/`.
- **English docs;** line length ≤ 100 where practical.

## Constraints and Assumptions

- Programming language: Python.
- Parent / source debt: PYPOST-853 (optional response status/body widget ids);
  also noted under PYPOST-889 (snapshot observation still walks the panel).
- Wait-for-text already exists as an agent capability; this story supplies
  the missing target identities, not a new wait primitive.
- Status and body text shown to users may differ in formatting from
  snapshot-sanitized values; identity-scoped waits should match what those
  surfaces actually display.
- “Optional” means finer-grained ids in addition to the panel root — not
  optional to ship the ids for this debt ticket’s acceptance.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval gate / no Jira updates in this step).

## Main Entities and Interactions

| Entity | Role / business attributes |
| --- | --- |
| AI agent / harness | Drives Send; waits for expected status/body text by identity |
| Response panel | Container surface with existing stable identity |
| Response status surface | Displays status text (e.g. HTTP code/phrase); needs own id |
| Response body surface | Displays body text (response payload as shown); needs own id |
| Text wait | Bounded wait until expected text appears on a named surface |
| Identity spot-check | CI proof that key identities exist on the UI |
| Golden / agent e2e | Automated Send → response confidence path |

Interaction overview:

1. Harness launches PyPost and reaches UI ready.
2. Harness drives a request Send that yields a response.
3. Harness waits for expected status text on the status identity.
4. Harness waits for expected body text on the body identity.
5. Spot-check and docs keep the new identities discoverable and regression-safe.
6. Panel root identity remains available for snapshots and migration.

## Q&A

- Q: Why not keep waiting only on the response panel snapshot?
  A: Panel walks couple readiness to sanitize form and mix status/body with
  other panel text. Dedicated ids enable targeted text waits and reduce
  flaky coupling.

- Q: Why are the id strings part of requirements?
  A: Jira acceptance names `pypost_response_status` / `pypost_response_body`
  as the stable contract agents will use; they are the business identity
  names, not an implementation sketch.

- Q: Must every sibling e2e migrate off panel walks in this ticket?
  A: No. Acceptance is ids + docs + spot-check; adoption by golden (and
  later siblings) is in scope where needed to prove text waits work.

- Q: Does this change what users see in the response UI?
  A: No. Visible status/body behaviour stays the same; only automation
  identities are added.

- Q: Why not only document the gap?
  A: Business value is actionable identities and CI spot-check, not a note
  that waits remain panel-coupled.

- Q: Jira / commit in this run?
  A: No — parent orchestrator owns Phase D/F.
