# PYPOST-890: Agent e2e matrix for Send/response presentation

## Goals

API testers and maintainers must trust that Send → response presentation
stays correct across common HTTP methods and request body shapes — not only
for the single edge case locked by sibling
[PYPOST-889](https://pypost.atlassian.net/browse/PYPOST-889). Bug
[PYPOST-887](https://pypost.atlassian.net/browse/PYPOST-887) showed incorrect
response presentation for one malformed / nested JSON-like body; similar
defects may hide in other method × body combinations.

This story’s business goal is to **systematically probe** those combinations
in the agent UI e2e suite: assert response presentation invariants (body
exactly once, status once and consistent with the stub, no duplicate
status+body blocks for one Send), **record which combinations fail** for
triage, and keep a fast smoke slice runnable under the standard agent e2e
entry. Findings feed sibling triage story
[PYPOST-891](https://pypost.atlassian.net/browse/PYPOST-891) under epic
[PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888).

## Programming Language

Python (`.cursor/lsr/do-python.md`) for the agent e2e matrix (pytest).
Brief developer documentation and findings artifact in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **regression guardian / CI gate**, I want a parametrized agent UI e2e
  matrix that checks response presentation invariants across methods and body
  shapes, so similar bugs to PYPOST-887 surface in CI before users see them.
- As a **scenario author / AI agent**, I want the matrix to reuse the existing
  agent e2e harness and shared HTTP stubs so I do not invent a parallel Send
  path or hit a live host.
- As a **triage owner (PYPOST-891)**, I want a durable findings artifact
  listing failing combinations so I can file focused fix Bugs without
  re-running discovery by hand.
- As a **maintainer**, I want the full matrix (or a documented slow subset)
  reachable via `make test-agent-e2e`, plus a fast smoke slice, and a short
  `doc/dev/` note linked from the agent e2e umbrella.
- As a **sibling of PYPOST-889**, I want this matrix to broaden coverage without
  duplicating or replacing the single PYPOST-887 lock scenario.

## Definition of Done

- A parametrized agent UI e2e matrix exists under the agent e2e suite and is
  runnable via `make test-agent-e2e` (marker `agent_e2e`), or a documented
  subset is used when the full matrix is too slow — then slow cases are marked
  appropriately and a fast smoke slice remains in the default run.
- The matrix covers at least HTTP methods GET, POST, PUT, PATCH, and DELETE.
- The matrix covers request body shapes: empty, valid JSON, malformed /
  extra-wrapped JSON-like, non-JSON text, and a large-ish body when feasible.
- For each combination exercised, the suite asserts response presentation
  invariants: response body text appears exactly once after one Send; status
  appears once and matches the stub; no duplicate status+body blocks for that
  Send.
- Combinations that fail are recorded (expected failures / xfail / collected
  findings list) so triage can file Bugs; a findings artifact lives under
  `ai-tasks/` or docs for PYPOST-891.
- The matrix prefers shared HTTP stubs (`stub_agent_e2e_http`); no live host
  is required for acceptance.
- Brief developer documentation lives under `doc/dev/` and is linked from the
  agent e2e umbrella docs.
- Product bugs discovered by the matrix are **not** fixed in this story
  (owned by triage / separate Bugs).
- The single PYPOST-887 lock remains owned by PYPOST-889 (out of scope here).

## Task Description

**Problem:** One known presentation defect (PYPOST-887) does not prove
correctness across the method × body space agents and users exercise. Without
a systematic matrix, similar incorrect behaviors can ship unnoticed.

**Business need:** An agent e2e matrix that probes common methods and body
shapes against response presentation invariants, surfaces failures for
triage, and stays discoverable and runnable under the standard suite entry —
without fixing product bugs in this story and without replacing the focused
PYPOST-889 lock.

### In Scope

- Parametrized agent UI e2e matrix for methods × body shapes × presentation
  invariants.
- At least GET / POST / PUT / PATCH / DELETE.
- Body shapes: empty, valid JSON, malformed / extra-wrapped JSON-like,
  non-JSON text, large-ish body if feasible.
- Invariants: body exactly once; status once and consistent with stub; no
  duplicate status+body blocks for a single Send.
- Prefer shared agent e2e HTTP stubs; deterministic outcomes; no live host.
- Record failing combinations for triage (findings artifact).
- Suite entry via `make test-agent-e2e`, with documented subset + fast smoke
  if the full matrix is too slow.
- Brief `doc/dev/` documentation linked from the agent e2e umbrella.
- Reuse of existing agent e2e harness capabilities (session, stub, ids,
  wait, snapshot) and patterns proven by PYPOST-889 where applicable.

### Out of Scope

- Fixing discovered product bugs (triage story PYPOST-891 and resulting Bugs).
- The single PYPOST-887 double-body lock scenario (sibling PYPOST-889).
- Changing product Send / response UX beyond what the matrix observes.
- Live-network verification against third-party hosts.
- User-facing product docs (`doc/user/`).
- Broadening beyond response presentation invariants (e.g. request editor
  UX, scripting, collections) unless required to drive Send.

## Functional Requirements

- FR1: Provide a parametrized agent UI e2e matrix marked for the agent e2e
  suite (`agent_e2e`) and included when `make test-agent-e2e` runs with
  defaults, **or** document a subset for the default run and keep a fast
  smoke slice green there while marking slower cases appropriately.
- FR2: The matrix exercises at least methods GET, POST, PUT, PATCH, and
  DELETE.
- FR3: The matrix exercises request body shapes: empty; valid JSON;
  malformed / extra-wrapped JSON-like; non-JSON text; and a large-ish body
  when feasible within suite time budgets.
- FR4: For each exercised combination, after Send settles, assert:
  - response body text appears exactly once in the response panel;
  - status is shown once and is consistent with the stub outcome;
  - there are no duplicate status+body blocks for that single Send.
- FR5: Combinations that violate invariants are recorded for triage
  (expected failure / xfail / findings list) rather than silently ignored.
- FR6: A findings artifact under `ai-tasks/` or docs lists failing
  combinations so PYPOST-891 can file fix Bugs.
- FR7: The matrix uses deterministic shared HTTP stubs (prefer
  `stub_agent_e2e_http`); no live host is required for acceptance.
- FR8: The matrix composes with the existing agent e2e harness (session,
  HTTP stub, widget identity, wait, snapshot) rather than a one-off
  parallel driver.
- FR9: Brief developer documentation under `doc/dev/` describes the matrix
  and links from the agent e2e umbrella documentation.
- FR10: Do not replace or remove the PYPOST-889 lock; this story adds
  breadth, not a substitute for the reported-case lock.

## Non-functional Requirements

- **Determinism:** No live external HTTP as the primary path; stubbed
  outcomes keep CI stable under offscreen Qt.
- **Suite time:** Prefer keeping a fast smoke slice in the default
  `make test-agent-e2e` run; full matrix may be documented as a slower
  subset if needed.
- **Clarity on failure:** Failures must make the violated invariant and the
  method × body combination obvious to a maintainer / triage owner.
- **Harness reuse:** Prefer existing agent e2e session / stub / identity /
  wait / snapshot vocabulary and PYPOST-889 lock patterns over new
  parallel tooling.
- **Timeouts:** New pytest tests declare explicit `pytest.mark.timeout` per
  `.cursor/lsr/do-testing.md`.
- **Make consistency:** Prefer `make test-agent-e2e` over undocumented
  shell-only recipes as the primary run entry.
- **Docs discoverability:** Matrix is findable from the agent e2e umbrella.
- **Triage handoff:** Findings artifact is usable by PYPOST-891 without
  requiring re-discovery runs to understand what failed.

## Constraints and Assumptions

- Parent epic: [PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888)
  (Agent e2e audit: Send/response presentation correctness).
- Blocks triage: [PYPOST-891](https://pypost.atlassian.net/browse/PYPOST-891)
  (Triage agent e2e audit findings and file fix Bugs).
- Related context: [PYPOST-887](https://pypost.atlassian.net/browse/PYPOST-887)
  motivated the audit; sibling lock
  [PYPOST-889](https://pypost.atlassian.net/browse/PYPOST-889) already covers
  the reported PUT + malformed body case.
- “Exactly once” / “status once” refer to the user-visible response panel
  after one Send (same surface PYPOST-887 / PYPOST-889 targeted).
- Product bug ownership stays with triage (PYPOST-891) and resulting Bugs;
  this story owns the matrix, findings recording, and documentation.
- Prefer shared stubs (`stub_agent_e2e_http`); inventing a separate stub
  stack is out of preference unless the shared stub cannot express a needed
  outcome.
- Labels: `agent-e2e`, `testing`.
- Step 1 review is treated as pre-approved under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Presentation matrix | Parametrized agent e2e probe of methods × bodies × invariants |
| Request combination | One HTTP method + one request body shape |
| HTTP stub outcome | Deterministic response; no live host |
| Response presentation | Response panel after one Send (body, status, blocks) |
| Presentation invariants | Body once; status once / stub-consistent; no duplicate blocks |
| Findings artifact | Record of failing combinations for PYPOST-891 triage |
| Fast smoke slice | Subset kept in default `make test-agent-e2e` when full matrix is slow |
| Agent e2e harness | Session, stub, ids, wait, snapshot |
| PYPOST-889 lock | Sibling single-case regression lock (not replaced) |
| Dev docs note | Discovers the matrix from agent e2e umbrella |

Interaction overview:

1. Matrix obtains a ready agent UI session via the existing harness.
2. For each method × body combination, the scenario prepares the request and
   installs a deterministic shared HTTP stub.
3. Scenario drives Send and waits until the response panel has settled.
4. Scenario asserts presentation invariants; failures are recorded for
   triage.
5. Suite entry runs the smoke slice (and documented full/slow subset as
   needed); findings artifact and docs support PYPOST-891 and authors.

## Q&A

- Q: Why a matrix if PYPOST-889 already locks PYPOST-887?
  A: The lock covers one reported case. The business need is broader: find
  **similar** incorrect presentation behaviors across methods and body
  shapes before users do.
- Q: Why not fix failing combinations in this story?
  A: Out of scope. This story discovers and records; PYPOST-891 triages and
  files fix Bugs.
- Q: Must every method × body cell run in the default `make test-agent-e2e`?
  A: Prefer yes; if too slow, document a subset, mark slow cases, and keep a
  fast smoke slice in the default run.
- Q: Does this replace the PYPOST-889 lock?
  A: No. FR10 — breadth complements the focused lock; do not remove it.
- Q: Must the original third-party reproduction URL be used?
  A: No. Business need is presentation correctness under stubbed Send; live
  host reachability is not required.
- Q: What if a body shape is infeasible (e.g. very large) under suite time?
  A: Include a large-ish body when feasible; if not, document the omission
  in architecture / findings rather than blocking the rest of the matrix.
- Q: Is Step 1 user approval required before Step 2?
  A: Under sprint-task-runner autonomy, Step 1 is treated as pre-approved;
  proceed without a separate approval gate.
