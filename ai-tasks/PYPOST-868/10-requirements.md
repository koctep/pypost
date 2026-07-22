# PYPOST-868: Optional URL→canned response router helper

## Goals

Agent e2e authors who need **more than one canned HTTP outcome in a single
scenario** (for example two Sends to different URLs) currently must write a
custom callable stub. That is powerful but easy to get wrong: match rules are
ad hoc, failures are opaque, and each scenario reinvents routing.

This debt item’s business goal is to make **multi-URL deterministic stubbing
easier and safer** — either by shipping a small optional URL→canned-response
router for the shared agent e2e HTTP layer, or by documenting a clear
**ENABLE vs DEFER** decision with proof that the current callable path remains
the supported escape hatch until multi-URL scenarios proliferate.

Source: [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859)
tech debt → [PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868).

## Programming Language

Python 3.10+ for helper and tests (`.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **scenario author / AI agent**, I want an optional way to map resolved
  URLs to canned responses so multi-Send flows stay deterministic without a
  hand-rolled callable.
- As a **maintainer**, I want match rules and failure behavior documented so
  routing mistakes are obvious and consistent.
- As a **pack owner**, I want single-canned and custom-callable paths to keep
  working unchanged so existing golden/env/seed scenarios do not regress.
- As a **desktop user** (indirect), I want no product UX change — this is
  test-harness hygiene only.

## Definition of Done

- An **ENABLE vs DEFER** decision is recorded in architecture and tech-debt
  artifacts (and reflected in developer docs).
- If **ENABLE**: an optional URL→canned-response router exists on the shared
  agent e2e HTTP stub path; automated tests prove multi-URL routing and safe
  miss behavior; docs describe match rules and usage.
- If **DEFER**: docs state why callable `side_effect` remains sufficient, when
  to revisit, and automated proof still locks the decision/contract the team
  chose for this ticket.
- Existing single-result and callable stub usage remains green.
- Steps 1–8 artifacts exist under `ai-tasks/PYPOST-868/`.
- No intentional product UX or live-network behavior change.

## Task Description

**Problem:** The shared deterministic HTTP layer (PYPOST-859) supports one
canned result or a custom callable. Authors with multi-URL Send flows have no
first-class map keyed by URL, so they reinvent routing in callables.

**Business need:** Close low-priority testing debt so multi-URL stub routing is
either first-class and documented, or explicitly deferred with a safe, documented
alternative — not left as tribal knowledge.

### In Scope

- Decide ENABLE vs DEFER for an optional URL→canned response router.
- If ENABLE: implement optional mapping on the shared stub helper, tests, and
  docs (match rules, miss behavior).
- If DEFER: document decision + revisit criteria; keep callable path as the
  supported multi-URL approach; provide appropriate red/green proof of the
  chosen contract.
- Preserve isolation (stub install/teardown) and CI determinism under
  offscreen Qt for agent flows that use the layer.
- Complete Steps 1–8 workflow artifacts.

### Out of Scope

- Redesigning the HTTP client, RequestWorker, or product Send path.
- Migrating golden/env/seed scenarios that only need a single canned result.
- Sibling debt (response-panel helper share, caplog install proof, seed POST
  GUI) owned by other tickets.
- Live external HTTP as the primary agent-flow path.
- User-facing product docs (`doc/user/`).

## Functional Requirements

- FR1: Record an ENABLE vs DEFER decision for the optional URL→canned router.
- FR2: If ENABLE, authors can install a multi-URL canned map via the shared
  stub entry without writing a custom callable for simple URL→result cases.
- FR3: If ENABLE, documented match rules define how a Send’s URL selects a
  canned result (and what happens on miss / ambiguity).
- FR4: Single canned result and callable stub modes continue to work.
- FR5: Automated tests cover the chosen contract (router behavior if ENABLE;
  decision/contract proof if DEFER).
- FR6: Developer docs for the agent e2e HTTP layer describe the decision and
  how to multi-URL stub safely.

## Non-functional Requirements

- **Minimalism:** Smallest optional helper that removes ad-hoc URL matching for
  simple maps; do not build a full HTTP mock server.
- **Isolation:** Stub install/teardown must not leak across tests.
- **Timeouts:** New/changed pytest tests declare explicit
  `pytest.mark.timeout` per `.cursor/lsr/do-testing.md`.
- **Discoverability:** Docs findable from `doc/dev/agent_e2e_http.md`.
- **No product impact:** Harness/test/docs only.

## Constraints and Assumptions

- Parent: [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859);
  debt note in `ai-tasks/PYPOST-859/60-tech-debt.md`.
- Shared HTTP layer and catalog already exist; this task only adds optional
  routing convenience (or documents deferral).
- Labels: `agent`, `e2e`, `tech-debt`, `testing`. Priority: Low. SP: 3.
- Autonomous batch: user approval gates pre-approved; no Jira updates or git
  commit from this execution.
- Research may conclude YAGNI (DEFER) if multi-URL scenarios have not
  proliferated and callable coverage is enough — still complete Steps 1–8.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Shared HTTP stub helper | Entry for deterministic agent e2e HTTP |
| Canned response | Named deterministic HTTP outcome |
| URL→canned router (optional) | Maps request URL to a canned outcome |
| Custom callable stub | Existing escape hatch for complex sequences |
| Scenario author | Writes multi-Send / multi-URL agent e2e |
| Developer docs | Match rules and ENABLE/DEFER guidance |

Interaction overview (ENABLE path):

1. Author builds a map of URL → canned response.
2. Shared stub installs routing for the test.
3. Each Send resolves to the matching canned outcome (or documented miss).
4. Tear-down restores the real send binding.

## Q&A

| Q | A |
| --- | --- |
| Why not always require a callable? | Callables work but recreate match logic; a map is safer for simple multi-URL cases. |
| Why allow DEFER? | Parent deferred until multi-URL scenarios proliferate; YAGNI may still apply. |
| Product impact? | None — test harness / docs only. |
| Source? | [PYPOST-859 tech debt](../PYPOST-859/60-tech-debt.md) → PYPOST-868. |
