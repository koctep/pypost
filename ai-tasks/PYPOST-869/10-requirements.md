# PYPOST-869: Share response-panel snapshot helpers across Send tests

## Goals

Agent Send / golden e2e scenarios (and related UI Send locks) each copy the
same response-panel snapshot helpers — walk values, find a named subtree,
build excerpts, and join panel text for ready predicates. Authors and
maintainers waste time keeping those copies in sync; small drifts make
timeout diagnostics and asserts diverge.

This story’s business goal is a **single shared helper surface** for
response-panel snapshot inspection so Send scenarios reuse one definition,
reduce drift risk as more Send cases land, and keep failure messages
consistent.

## Programming Language

Python (`.cursor/lsr/do-python.md`) for shared helpers and test rewires.
Developer docs in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **scenario author / AI agent**, I want one place to import
  response-panel snapshot helpers so new Send tests do not copy-paste
  walk / subtree / excerpt logic.
- As a **maintainer**, I want golden, env Send, double-body lock, and
  presentation-matrix scenarios to share the same helpers so a fix or
  improvement lands once.
- As a **CI reader**, I want timeout / assert excerpts to stay consistent
  across those scenarios after the share.

## Definition of Done

- Shared response-panel snapshot helpers exist under `tests/helpers/`
  (name may follow architecture; intent is a dedicated helper module).
- Golden, env HTTP Send, double-body lock, and presentation-matrix Send
  modules import those helpers instead of defining local duplicates of
  walk / subtree / excerpt (and related join helpers where duplicated).
- Automated proof that the shared surface exists and behaves as expected
  (unit-level on a tiny fake tree; no product UI change).
- Existing Send e2e scenarios remain green under the project agent-e2e
  make target (targeted runs acceptable for verification).
- Developer docs mention the shared helpers for authors writing Send
  waits / asserts.
- No change to product runtime behavior or HTTP stub catalog.

## Task Description

**Problem:** `_walk_values`, `_subtree_by_name`, and related ready /
excerpt helpers are duplicated across Send e2e modules (see parent debt
note in [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859)
`60-tech-debt.md`).

**Business need:** Extract and rewire so Send tests share one helper
module and stop drifting.

### In Scope

- Extract walk / subtree / excerpt / joined-panel helpers used by Send
  snapshot waits and asserts.
- Rewire golden, env Send, double-body, and presentation-matrix modules.
- Unit proof for the shared helpers; keep existing e2e green.
- Dev docs update for authors.

### Out of Scope

- Product UI, RequestWorker, or HTTP stub catalog changes.
- Changing Send settle timeouts into a shared constant (optional later
  debt; not required for AC).
- User-facing product docs (`doc/user/`).
- Creating Jira Debt tickets from this task’s Step 7 (orchestrator Phase D
  owns ticket creation; this run documents follow-ups only).

## Functional Requirements

- FR1: A shared helper module under `tests/helpers/` exposes walk,
  subtree-by-name, response-panel excerpt, and joined panel values (or
  equivalent names) for UI snapshot dict trees.
- FR2: Golden Send, env HTTP Send, double-body lock, and presentation
  matrix modules no longer define private copies of those helpers; they
  import the shared module.
- FR3: Helpers preserve today’s behavior for empty panels, missing
  `RESPONSE_PANEL`, excerpt truncation, and value joining used by ready
  predicates / asserts.
- FR4: Automated test proves the shared module is importable and
  exercises helpers on a small synthetic snapshot tree.
- FR5: Rewired agent Send scenarios remain passing (same external
  behavior).
- FR6: Developer documentation points authors at the shared helpers.

## Non-functional Requirements

- **Timeouts:** New/changed pytest tests declare explicit
  `pytest.mark.timeout` per `.cursor/lsr/do-testing.md`.
- **Minimalism:** Test-only change; no production package API.
- **Consistency:** Prefer public helper names without leading underscore
  in the shared module; call sites may keep thin local ready predicates
  that encode scenario-specific expected status/body tokens.
- **Line length / style:** Follow project Python and Markdown guides.

## Constraints and Assumptions

- Parent debt from [PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859);
  issue [PYPOST-869](https://pypost.atlassian.net/browse/PYPOST-869).
- Suggested path in debt note:
  `tests/helpers/agent_e2e_response_panel.py` (architecture may confirm).
- Known duplicate sites today:
  `tests/test_agent_golden_e2e.py`,
  `tests/test_agent_e2e_http_env.py`,
  `tests/test_agent_e2e_double_response_body.py`,
  `tests/test_agent_e2e_presentation_matrix.py`.
- Step reviews treated as pre-approved under sprint-task-runner autonomy
  for this Task (no Jira MCP; no git commit).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Shared response-panel helpers | One definition of walk / subtree / excerpt / join |
| Send e2e scenario modules | Import helpers; keep scenario-specific ready asserts |
| Synthetic unit proof | Validates helper behavior without a live Qt window |
| Developer docs | Tell authors where to import helpers |

Interaction overview:

1. Author imports shared helpers in a Send scenario.
2. After Send, wait/assert uses walk / subtree / excerpt on a snapshot.
3. Unit proof exercises the same helpers on a fake tree.
4. Docs point new scenarios at the shared module.

## Q&A

- Q: Why share helpers instead of leaving copies?
  A: Drift risk and duplicated timeout diagnostics as more Send scenarios
  land (stated parent debt).
- Q: Why include presentation matrix and double-body, not only golden/env?
  A: Same duplicated helpers; sharing once covers all current Send
  snapshot consumers and matches the ticket’s “across Send tests” scope.
- Q: Must scenario-specific `_response_ready` move into the shared module?
  A: No — ready predicates encode expected status/body tokens per
  scenario. Sharing walk / subtree / excerpt / join is enough.
- Q: Any product behavior change?
  A: No — test harness hygiene only.
