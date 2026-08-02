# PYPOST-976: Session body-editor keyClicks smoke

## Goals

Agent and golden-flow authors rely on opt-in keystroke-realism fill when driving
the product request body. [PYPOST-945](https://pypost.atlassian.net/browse/PYPOST-945)
closed fixture proofs for plain and rich text editors, and an existing agent
e2e session smoke already covers keystroke fill on the URL field. The live
product request body editor under a full agent e2e session was explicitly
deferred as optional hardening (UT-1 in
[PYPOST-945/60-tech-debt.md](../PYPOST-945/60-tech-debt.md)).

Without a session-level smoke, maintainers cannot be sure that opt-in
keystroke fill leaves the expected plain text in the real request body area
when the full product UI is running. Regressions that only appear in the live
body editor would slip past fixture and URL-field proofs and weaken confidence
in agent drive scripts that type request payloads.

The business goal is optional end-to-end confidence: a bounded, offscreen
agent e2e proof that keystroke-realism fill on the request body editor leaves
matching plain text, with no live network dependency. This closes the Lowest
priority Debt follow-up from PYPOST-945. Labels: `agent`, `e2e`, `tech-debt`.

## Programming Language

Python with PySide6. Task artifacts and developer documentation use English
Markdown.

## User Stories

- As an **agent / e2e author**, I want confidence that opt-in keystroke fill
  on the live request body editor leaves the expected plain text so drive
  scripts that type payloads are backed by CI.
- As a **maintainer**, I want a session smoke that complements fixture and
  URL-field keyClicks proofs so body-editor regressions are caught early.
- As a **CI owner**, I want the proof under the established agent e2e path
  with explicit timeouts, offscreen execution, and no live network so the
  suite stays bounded and green.
- As a **golden-flow owner**, I want no change to default fill behaviour or
  existing happy-path agent e2e scenarios unless a real defect is found.

## Definition of Done

- An agent e2e session smoke fills the request body editor using opt-in
  keystroke-realism fill and asserts the body plain text matches the intended
  value (Jira acceptance: “Session body-editor keyClicks smoke green”).
- The proof runs without requiring live network access beyond what the
  harness already allows for offscreen agent e2e.
- Existing fixture keyClicks proofs, URL-field session keyClicks smoke, and
  unrelated agent e2e coverage remain passing and unchanged in meaning.
- Steps 1–8 workflow artifacts exist under `ai-tasks/PYPOST-976/`.
- No intentional product runtime change beyond locking behavioral coverage
  (unless a smoke reveals a real defect — fix belongs in later steps).

## Task Description

### Problem

Keystroke-realism fill is proven on isolated fixtures (line, plain, and rich
text editors) and on the URL field inside an agent e2e session. The same
opt-in path on the product request body editor under a live session was left
out of scope for PYPOST-945. Authors who fill request bodies via keystroke
realism therefore lack session-level CI confidence for that field.

### Business Reason

Optional hardening — close the UT-1 gap so the agent harness has a live
request-body keystroke fill smoke without expanding into golden HTTP flows or
live network sends.

### In Scope

- Agent e2e session smoke: opt-in keystroke fill on the request body editor;
  assert resulting plain text matches.
- Offscreen execution under the agent e2e marker / session path with explicit
  timeouts.
- Complete Steps 1–8 workflow artifacts.
- Optional cross-links in developer docs (Step 8) if the smoke adds a new
  documented proof point.

### Out of Scope

- Production changes to fill behaviour, widgets, or session mirror unless a
  smoke reveals a real defect (fix belongs in later steps).
- Caplog or logging scalar asserts for body-editor keystroke fill
  ([PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977)).
- Per-keystroke signal emission counting on the body editor
  ([PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) scope).
- Per-key delay kwarg behaviour
  ([PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947)).
- Live HTTP send, golden seed POST flows, or any proof that requires live
  network.
- Replacing or weakening existing fixture or URL-field keyClicks proofs.
- Broad agent e2e suite redesign or unrelated cleanup.
- Jira ticket creation, commit, or status transitions (orchestrator).

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Agent e2e session smoke uses opt-in keystroke-realism fill on the request body editor. |
| FR2 | After fill, the request body plain text equals the intended fill string. |
| FR3 | Proof uses a ready agent e2e session with the request body editor reachable and interactable. |
| FR4 | Proof does not depend on live network access. |
| FR5 | Existing fixture keyClicks, URL-field session keyClicks, and unrelated agent e2e tests remain green. |

## Non-Functional Requirements

| ID | Requirement |
| --- | --- |
| NFR1 | Test-only change expected; no product runtime change unless a defect is found. |
| NFR2 | Explicit pytest timeout protection on the new proof. |
| NFR3 | Offscreen agent e2e execution; deterministic under CI. |
| NFR4 | English documentation; line length ≤ 100 where practical. |
| NFR5 | Optional hardening only; minimal scope beyond the body-editor session smoke. |

## Constraints and Assumptions

- Source debt: PYPOST-945 UT-1 — session body-editor keyClicks smoke deferred
  when fixture plain/rich proofs were delivered.
- Opt-in keystroke fill and session mirror already exist from
  [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917); this task adds
  coverage, not a new fill mode.
- URL-field session keyClicks smoke is the sibling pattern for session-level
  proof; body editor is the remaining gap.
- Request body editor may require the body area to be visible or selected in
  the session before fill; harness setup belongs to later steps.
- Sprint-task-runner batch: autonomous progression; no user approval gates in
  this subagent run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Agent / harness | Drives named UI after session ready |
| Agent e2e session | Hosts live product UI for bounded proofs |
| Request body editor | Multi-line field where HTTP payloads are edited |
| Opt-in keystroke fill | Whole-string fill delivered as typed characters |
| Plain text assertion | Confirms body content matches intent after fill |
| Session smoke | Lightweight live proof complementing fixture tests |
| CI / maintainers | Rely on green agent e2e and fixture suites |

## Q&A

| Q | A |
| --- | --- |
| Why is this needed if PYPOST-945 added plain/rich fixture proofs? | Fixtures lock editor types in isolation; this debt asks for the live product request body under agent e2e. |
| Why not cover this in PYPOST-945? | PYPOST-945 matched line-edit fixture scope; session body was explicitly deferred as UT-1. |
| Must the proof send HTTP or use golden seed flows? | No — fill and plain-text assert only; no live network. |
| Does caplog for body keystroke fill belong here? | No — [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977). |
| Product impact? | None expected — coverage debt unless smoke finds a regression. |
| Jira / commit in this run? | No — parent orchestrator owns later phases. |
