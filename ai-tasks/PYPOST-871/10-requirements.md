# PYPOST-871: Seed POST GUI Send scenario on shared HTTP layer

## Goals

The shared agent-e2e HTTP catalog already ships a seed POST canned response,
but no GUI Send scenario exercises that path. Authors and CI therefore have
no automated proof that a POST request (with body) can be driven through the
agent UI and land on the same deterministic stub used for seed GET / golden.

This story’s business goal is a **marked agent e2e GUI Send scenario** that
fills method, URL, and request body, Sends under the shared HTTP stub with
the seed POST canned result, and asserts status and body in the response
panel — closing the catalog-only gap called out from PYPOST-859.

## Programming Language

Python (`.cursor/lsr/do-python.md`) for the scenario test. Developer docs in
English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **scenario author / AI agent**, I want a seed POST Send example that
  mirrors the seed GET env Send pattern so I can copy a proven POST + body
  flow on the shared HTTP layer.
- As a **maintainer**, I want CI to prove seed POST catalog entry works
  end-to-end through the real UI → RequestWorker path (not only unit
  inventory).
- As a **reader of failure diagnostics**, I want status/body asserts and
  wait timeouts to reuse the shared response-panel helpers so messages stay
  consistent with other Send scenarios.

## Definition of Done

- A marked `agent_e2e` GUI Send scenario exists that:
  - drives method POST, seed POST URL, and a request body via stable UI
    identities;
  - wraps Send with the shared HTTP stub using the seed POST canned
    catalog entry;
  - asserts response status and canned body appear in the response panel.
- Scenario reuses shared response-panel snapshot helpers (PYPOST-869) where
  applicable; does not duplicate walk / subtree / join helpers.
- Explicit `pytest.mark.timeout` per testing guidelines; bounded wait for
  Send settle.
- Scenario is green under the project agent-e2e make target (targeted run
  acceptable for verification).
- Developer docs mention the seed POST Send scenario for authors.
- No change to product runtime behavior beyond test/docs (stub catalog
  already contains the canned entry).

## Task Description

**Problem:** `CANNED_SEED_POST_OK` is in the shared catalog but no agent
e2e Send exercises the POST body path via that stub
([PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859)
`60-tech-debt.md` →
[PYPOST-871](https://pypost.atlassian.net/browse/PYPOST-871)).

**Business need:** Close the inventory gap with one GUI Send scenario
mirroring env GET Send, with care for the POST body fill path.

### In Scope

- One agent e2e scenario: method/URL/(body) fill → shared stub → Send →
  status/body assert.
- Reuse of shared HTTP catalog/stub and response-panel helpers.
- Dev docs update pointing authors at the new scenario.

### Out of Scope

- New catalog entries or changes to stub install behavior (unless a tiny
  test-only constant export is required for clarity).
- Collection-tree navigation to open the seeded POST item (env GET also
  fills resolved URL rather than opening the tree).
- URL→response router (owned by sibling debt).
- User-facing product docs (`doc/user/`).
- Creating Jira Debt tickets from this task’s Step 7 (orchestrator Phase D
  lists follow-ups only; this run does not call Jira MCP).

## Functional Requirements

- FR1: An `agent_e2e`-marked GUI Send test exercises POST with a request
  body filled through the stable request-body identity.
- FR2: The test uses the shared HTTP stub with the existing seed POST
  canned catalog entry (same layer as seed GET / golden).
- FR3: After Send, the response panel shows the expected success status
  and the canned seed POST response body.
- FR4: Method and URL are filled via stable identities (POST + seed POST
  resolved URL).
- FR5: Response wait/assert reuse shared response-panel helpers (no local
  walk / subtree / join duplicates).
- FR6: Developer documentation lists the seed POST Send scenario for
  authors extending HTTP e2e coverage.

## Non-functional Requirements

- **Timeouts:** Module or test declares explicit `pytest.mark.timeout`;
  Send settle wait is bounded (mirror env GET settle budget unless
  architecture justifies otherwise).
- **Determinism:** No live network; stub at the shared send boundary.
- **Minimalism:** Prefer a new test module or clearly named test alongside
  env Send; avoid product UI changes.
- **Line length / style:** Follow project Python and Markdown guides.

## Constraints and Assumptions

- Parent debt from
  [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859); issue
  [PYPOST-871](https://pypost.atlassian.net/browse/PYPOST-871).
- Estimation context: deliverable is essentially one agent_e2e GUI Send
  scenario mirroring `tests/test_agent_e2e_http_env.py`, with care for
  POST body path (`REQUEST_BODY_EDIT` / helpers from PYPOST-869 /
  presentation matrix).
- Seed inventory and `CANNED_SEED_POST_OK` already exist.
- Step reviews treated as pre-approved under sprint-task-runner autonomy
  for this Task (no Jira MCP; no git commit).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Seed POST canned response | Deterministic stub result for POST Send |
| Shared HTTP stub | Installs canned result at send boundary |
| Agent GUI session | Blank or seeded session; UI fill + Send |
| Request body control | Stable identity for POST body fill |
| Response panel | Observed status + body for asserts |
| Shared panel helpers | Walk / subtree / join for waits and asserts |

Interaction overview:

1. Session opens with UI ready.
2. Author (test) fills URL, selects POST, fills request body.
3. Shared stub installs seed POST canned result.
4. Test clicks Send; waits until panel shows status + body.
5. Asserts confirm status label and canned body text.

## Q&A

- Q: Why a GUI Send scenario if the catalog already has seed POST?
  A: Catalog-only coverage does not prove UI → body → RequestWorker →
  stub composition; that is the debt called out in PYPOST-859.
- Q: Why mirror env GET rather than open the collection tree POST item?
  A: Env GET deliberately fills the resolved URL to avoid owning
  collection-tree navigation; same scope boundary applies.
- Q: Must the session be seeded?
  A: Either blank `agent_e2e_session` or seeded is acceptable if URL /
  method / body are filled explicitly; architecture chooses the simpler
  path that still proves POST body.
- Q: Any product behavior change?
  A: No — test + docs only; catalog entry already exists.
