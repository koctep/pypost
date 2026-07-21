# PYPOST-889: Agent e2e lock for double response-body regression

## Goals

API testers must trust that after Send, the response body appears **exactly
once**. Bug [PYPOST-887](https://pypost.atlassian.net/browse/PYPOST-887)
showed duplication for a PUT with a malformed / nested JSON-like request
body (`{ { "data": { } } }`). That defect undermines debugging trust even
when the product fix has landed.

This story’s business goal is to **lock that regression in the agent UI e2e
suite**: an automated scenario must drive the reported Send case (no live
host), assert single body presentation in the response panel, fail clearly
on the buggy double-body behavior, and stay green once the fix holds. The
lock protects the sprint goal of trustworthy Send/response presentation
under epic
[PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888).

## Programming Language

Python (`.cursor/lsr/do-python.md`) for the agent e2e scenario (pytest).
Brief developer documentation in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **regression guardian / CI gate**, I want an agent UI e2e scenario
  that fails when the PYPOST-887 double response-body bug returns, so the
  pipeline catches presentation corruption before users do.
- As a **scenario author / AI agent**, I want that lock to reuse the existing
  agent e2e harness (session, HTTP stub, widget ids, wait/snapshot) so I do
  not invent a parallel Send path or hit a live host.
- As a **maintainer**, I want a short `doc/dev/` note (linked from agent e2e
  / golden docs) so authors know this regression lock exists and how it fits
  the suite.
- As a **bug owner of PYPOST-887**, I want this story linked as Relates to
  that bug so the automated proof stays discoverable from the defect.

## Definition of Done

- An agent UI e2e scenario exists under the agent e2e suite and is runnable
  via `make test-agent-e2e` (marker `agent_e2e`).
- The scenario drives Send with the reported method and body shape, using a
  deterministic HTTP stub (no live host).
- After Send settles, the scenario asserts the response panel shows the
  response body **exactly once** (not duplicated).
- While the PYPOST-887 double-body behavior is present, the scenario fails
  clearly for that reason; after the fix, it passes.
- The scenario uses the existing agent e2e harness: session fixture, HTTP
  stub helper, stable widget ids, wait, and snapshot observation.
- Brief developer documentation lives under `doc/dev/` and is linked from
  agent e2e and/or golden docs as appropriate.
- Jira link Relates to PYPOST-887 is present (already on the issue; keep it).

## Task Description

**Problem:** PYPOST-887’s double response-body presentation after Send (PUT
+ malformed nested JSON-like body) needs a durable automated lock in agent
UI e2e. Unit-level coverage for the fix alone does not prove the full
Send → response-panel path an agent drives.

**Business need:** One focused agent e2e regression scenario that encodes
the reported case, fails on duplication, and stays green when single
presentation holds — without broadening into a matrix of methods/bodies.

### In Scope

- One agent UI e2e scenario for the reported PUT + body shape.
- Deterministic HTTP stub for Send (no live external host).
- Assertion that the response panel body appears exactly once.
- Red-on-bug / green-after-fix behavior relative to PYPOST-887.
- Use of existing agent e2e harness capabilities (session, stub, ids,
  wait, snapshot).
- Brief `doc/dev/` documentation and cross-links from agent e2e / golden
  docs.
- Maintain Relates link to PYPOST-887.

### Out of Scope

- Fixing the product double-body bug itself (owned by PYPOST-887).
- Broad method/body matrix coverage (sibling work under epic PYPOST-888).
- Changing product Send/response UX beyond what the lock observes.
- Live-network verification against the original third-party URL.
- User-facing product docs (`doc/user/`).

## Functional Requirements

- FR1: Provide an agent UI e2e scenario marked for the agent e2e suite
  (`agent_e2e`) and included when `make test-agent-e2e` runs with defaults.
- FR2: The scenario configures a request with method PUT and a raw body of
  the reported shape `{ { "data": { } } }` (malformed / nested JSON-like).
- FR3: The scenario sends the request through the agent UI path with a
  deterministic HTTP stub; no live host is required for acceptance.
- FR4: After Send settles, the scenario observes the response panel and
  asserts the response body content appears exactly once (not twice /
  duplicated).
- FR5: The assertion must fail while the PYPOST-887 double-body defect is
  present and pass when single presentation is restored.
- FR6: The scenario must compose with the existing agent e2e harness
  (session, HTTP stub, widget identity, wait, snapshot) rather than a
  one-off parallel driver.
- FR7: Brief developer documentation under `doc/dev/` describes the lock and
  links from agent e2e and/or golden documentation as appropriate.
- FR8: Keep the Jira Relates relationship to PYPOST-887.

## Non-functional Requirements

- **Determinism:** No live external HTTP as the primary path; stubbed
  outcomes keep CI stable under offscreen Qt.
- **Clarity on failure:** Failure message / assert should make double-body
  vs single-body obvious to a maintainer.
- **Minimalism:** One focused regression lock for the reported case; not a
  broad presentation matrix (that belongs under PYPOST-888 siblings).
- **Harness reuse:** Prefer existing agent e2e session / stub / identity /
  wait / snapshot vocabulary over new parallel tooling.
- **Timeouts:** New pytest tests declare explicit `pytest.mark.timeout` per
  `.cursor/lsr/do-testing.md`.
- **Make consistency:** Prefer `make test-agent-e2e` over undocumented
  shell-only recipes as the primary run entry.
- **Docs discoverability:** Lock is findable from the agent e2e umbrella
  and/or golden docs.

## Constraints and Assumptions

- Parent epic: [PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888)
  (Agent e2e audit: Send/response presentation correctness).
- Related bug: [PYPOST-887](https://pypost.atlassian.net/browse/PYPOST-887)
  (Relates already linked on this issue).
- Reported reproduction context (business trigger, not live dependency):
  PUT, body `{ { "data": { } } }`; original URL was a reproduction host
  only — automated proof must not require that host.
- “Exactly once” means the user-visible response panel body after one Send
  is not duplicated for that send (same surface PYPOST-887 targeted).
- Product fix ownership stays with PYPOST-887; this story owns the agent
  e2e lock and its documentation.
- Labels: `agent-e2e`, `testing`.
- Step 1 review is treated as pre-approved under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Regression lock scenario | Agent e2e proof of single vs double body |
| Request (reported case) | PUT + malformed nested JSON-like body |
| HTTP stub outcome | Deterministic response; no live host |
| Response presentation | Response panel body after one Send |
| Agent e2e harness | Session, stub, ids, wait, snapshot |
| Agent e2e suite entry | `make test-agent-e2e` / `agent_e2e` marker |
| PYPOST-887 | Related bug being locked against regression |
| Dev docs note | Discovers the lock from agent e2e / golden |

Interaction overview:

1. Scenario obtains a ready agent UI session via the existing harness.
2. Scenario prepares the reported PUT + body shape and installs a
   deterministic HTTP stub.
3. Scenario drives Send and waits until the response panel has settled.
4. Scenario asserts the response body appears exactly once.
5. Suite entry (`make test-agent-e2e`) runs the lock with other agent e2e
   scenarios; docs point authors to it.

## Q&A

- Q: Why an agent e2e lock if PYPOST-887 already has (or had) a unit repro?
  A: The business need is to prove the full agent-driven Send → response
  panel path, not only an internal presenter unit. Agents and CI must see
  the same surface users watch after Send.
- Q: Why not fix the bug in this story?
  A: Product correction is PYPOST-887. This story only locks the regression
  so it cannot silently return.
- Q: Why not cover many methods and body shapes here?
  A: Out of scope — broad matrix belongs under epic PYPOST-888 siblings.
  This story locks the reported case only.
- Q: Must the original third-party URL be used?
  A: No. Business need is single vs double presentation with the reported
  method/body; live host reachability is not required.
- Q: What does “exactly once” mean if the stub body is empty or short?
  A: The stub must return a recognizable body so duplication is detectable;
  the assertion counts presentation of that body in the response panel,
  not whether the request body was valid JSON.
- Q: Is Relates to PYPOST-887 still required if already linked?
  A: Yes as DoD — keep the existing Relates link; do not drop it.
