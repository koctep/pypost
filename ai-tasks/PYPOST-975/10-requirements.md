# PYPOST-975: Live collection-tree negative select via agent e2e

## Goals

Agent and golden-flow authors rely on select actions against the product
collection tree. [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942)
locked clear missing-option and out-of-range failures for list and tree
controls in the offscreen fixture suite. That proves the agent API contract,
but does not exercise the live product collection tree under a full agent e2e
session.

Without a live proof (or an explicit documented deferral), authors and
maintainers cannot be sure that invalid collection-tree selects fail with the
same actionable errors when the real tree is present. Silent mis-selection or
ambiguous failures would slow drive-script fixes and weaken CI triage.

The business goal is optional hardening confidence: either an agent e2e proof
that missing and out-of-range collection-tree options fail clearly on the live
tree, or a written deferral that records why the harness cannot host that proof
yet. This is the Low-priority, 3-story-point Debt follow-up recorded as TD-2 in
[PYPOST-942/60-tech-debt.md](../PYPOST-942/60-tech-debt.md). Labels: `agent`,
`e2e`, `tech-debt`.

## Programming Language

Python with PySide6. Task artifacts and developer documentation use English
Markdown.

## User Stories

- As an **agent / e2e author**, I want a missing collection-tree label on the
  live tree to fail with an explicit “option not found” style error so I can
  fix drive scripts against the real product UI.
- As an **agent / e2e author**, I want an out-of-range collection-tree index on
  the live tree to fail with an explicit out-of-range error so bad indices do
  not slip through agent e2e runs.
- As a **maintainer**, I want live collection-tree negative select behaviour
  either locked by agent e2e coverage or explicitly deferred with a documented
  harness gap so the debt is not left ambiguous.
- As a **CI owner**, I want any new agent e2e proofs to run under the established
  agent e2e path with explicit timeouts so the suite stays bounded and green.
- As a **failure-triage owner**, I want live-tree failures to match the same
  actionable pattern already proven in the fixture suite so logs stay consistent.

## Definition of Done

Either outcome below satisfies Done (Jira acceptance allows both):

**Path A — live proof**

- Agent e2e asserts a clear, actionable error when a select targets a missing
  display label on the live product collection tree.
- Agent e2e asserts a clear, actionable error when a select uses an out-of-range
  index on the live product collection tree.
- Existing fixture-suite list/tree negative select and agent e2e happy-path
  coverage remain passing and unchanged in meaning.

**Path B — documented deferral**

- A task artifact (and any required developer note) records why live
  collection-tree negative select cannot be hosted yet (harness gap), what
  fixture coverage already proves, and what would unblock a future live proof.
- No false claim that live negative select is covered.

In both paths:

- No production UI, public API, logging, or metric behaviour changes unless a
  live proof reveals a real defect (then fix belongs in later steps).
- Unticketed follow-ups, if any, live only in this task’s `60-tech-debt.md`.

## Task Description

### Problem

PYPOST-942 closed dedicated negative-path fixture tests for list and tree
select (missing label and out-of-range index). Live product collection-tree
negative select under an agent e2e session was explicitly deferred as optional
hardening. Authors who drive the real collection tree therefore lack
agent-e2e-level confidence that invalid selects fail clearly outside synthetic
fixtures.

### Business Reason

Optional end-to-end confidence that invalid collection-tree selects fail with
the same actionable errors against the live product tree — or an honest
documented deferral if the harness cannot host that proof — so this Low debt
item is closed without leaving the gap unspoken.

### In Scope

- Decide and deliver one of:
  - Agent e2e coverage that asserts clear errors for missing and/or out-of-range
    collection-tree select targets on the live collection tree; or
  - Documented deferral of that live proof when harness gaps block it.
- Keep any live proof within the established agent e2e session / marker path
  with explicit timeouts.
- Preserve existing fixture negative-select and agent e2e contracts.

### Exclusions

- Changing production widgets, widget identities, or product UI for its own
  sake.
- Altering select behaviour or error message wording unless a proof reveals a
  defect (fix belongs in later steps).
- Replacing or redesigning the fixture-suite list/tree negative tests from
  PYPOST-942 (they remain the API contract baseline).
- Combo out-of-range index coverage (owned by
  [PYPOST-974](https://pypost.atlassian.net/browse/PYPOST-974)).
- Item-view / `QListView` negative paths (owned by related tickets such as
  PYPOST-939 / PYPOST-972).
- Nested tree index out-of-range beyond the existing top-level index contract.
- Broad agent e2e suite redesign or unrelated cleanup.
- Jira ticket creation, commit, or status transitions (orchestrator).

## Functional Requirements

- **FR-1:** When Path A is chosen, a select with unknown display text on the
  live collection tree must fail with an actionable error indicating the option
  was not found.
- **FR-2:** When Path A is chosen, a select with an invalid top-level index on
  the live collection tree must fail with an actionable error indicating the
  index is out of range.
- **FR-3:** When Path A is chosen, at least one dedicated agent e2e proof must
  cover missing-option and/or out-of-range behaviour on the live collection
  tree (both preferred; one case plus documented residual gap is acceptable if
  harness limits apply).
- **FR-4:** Live-tree failure messaging must follow the same actionable pattern
  already used by fixture list/tree negative select (`option not found` /
  `option index out of range` style).
- **FR-5:** When Path B is chosen, requirements and follow-up notes must state
  the harness gap, cite existing fixture coverage as the current contract, and
  avoid claiming live negative select is proven.
- **FR-6:** Existing PYPOST-942 fixture negative select tests and unrelated
  agent e2e scenarios must retain their current meaning and stay green.
- **FR-7:** Developer troubleshooting guidance that documents collection-tree
  or select errors must remain accurate for whichever path is delivered.

## Non-Functional Requirements

- **NFR-1 — Compatibility:** Behaviour-preserving for callers; no new public
  API surface unless a proven defect forces a minimal fix.
- **NFR-2 — Stability:** Any new agent e2e proof must be deterministic under
  the offscreen agent e2e path, with explicit pytest timeouts and no live
  network requirement beyond what the harness already allows.
- **NFR-3 — Maintainability:** Prefer a focused negative-path proof (or a short
  deferral note) over broad suite expansion.
- **NFR-4 — Observability:** No new log or metric requirements.
- **NFR-5 — Scope control:** Optional hardening only; keep changes limited to
  live collection-tree negative select confidence or its documented deferral.

## Acceptance Criteria

- **AC-1:** Either agent e2e asserts a clear error for a missing collection-tree
  option on the live tree, or Path B documents why that case is deferred.
- **AC-2:** Either agent e2e asserts a clear error for an out-of-range
  collection-tree option/index on the live tree, or Path B documents why that
  case is deferred.
- **AC-3:** If Path A is delivered, proofs run under the agent e2e marker /
  session path with explicit timeout protection.
- **AC-4:** Fixture-suite list/tree negative select coverage from PYPOST-942
  remains green and is not removed or weakened.
- **AC-5:** No user-visible product behaviour, public interface, logging schema,
  or metric changes unless a proven defect is found.
- **AC-6:** Closes PYPOST-942 TD-2 (live collection-tree negative select via
  agent e2e session, or documented deferral).

## Constraints and Assumptions

- Source debt: PYPOST-942 TD-2 — optional live collection-tree negative select
  via agent e2e session beyond the fixture suite.
- Fixture negative-select error behaviour already exists and is test-backed;
  this task adds live confidence or documents why it cannot.
- Tree index select applies to top-level rows only (PYPOST-916 / PYPOST-942
  contract); nested rows are selected by display text.
- Jira acceptance explicitly allows documented deferral if harness gaps block
  a live proof.
- Sprint-task-runner batch: autonomous progression; no user approval gates in
  this subagent run.
- Parent PYPOST-942 is Done; this ticket closes the optional live-hardening
  follow-up.

## Main Entities and Interactions

| Entity | Business role | Required outcome |
| --- | --- | --- |
| Agent / harness | Drives named UI after ready | Clear failure or documented gap |
| Agent e2e session | Hosts live product UI for e2e | Can host negative select or not |
| Collection tree | Live product hierarchical list | Invalid select fails clearly |
| Select action | Chooses one row by label or index | Rejects missing / out-of-range |
| Display text | Visible label used to find a row | Unknown label → actionable error |
| Index | Zero-based top-level position | Out of range → actionable error |
| Actionable error | Failure the author can fix | Pattern matches fixture suite |
| Documented deferral | Honest record of harness limits | Gap not left unspoken |
| CI / maintainers | Rely on e2e and fixture proofs | Live proof or clear deferral |

Interaction overview (Path A):

1. An agent e2e scenario opens a ready session with the live collection tree.
2. A harness issues a select with a missing label or invalid top-level index.
3. The agent API rejects the call with an actionable error.
4. Automated proof asserts that failure under timeout protection.
5. Fixture negative-select tests remain green.

Interaction overview (Path B):

1. Investigation shows the agent e2e harness cannot host live negative select
   yet (gap recorded).
2. Deferral notes cite fixture coverage as the current contract.
3. TD-2 closes without claiming live proof.

## Evidence and Traceability

| Evidence | Current observation | Requirement impact |
| --- | --- | --- |
| PYPOST-942 TD-2 | Optional live collection-tree negative select | Goals, AC-6 |
| PYPOST-942 DoD / out of scope | Live `COLLECTION_TREE` agent e2e deferred | Problem statement |
| Jira PYPOST-975 | Assert clear error or documented deferral | AC-1, AC-2, Path A/B |
| Fixture list/tree negative tests | API contract already locked | FR-6, AC-4 |
| Sibling PYPOST-974 | Combo index parity; separate debt | Exclusions |

## Risks

| Risk | Consequence | Requirement guard |
| --- | --- | --- |
| Live proof never attempted or deferred vaguely | Debt remains ambiguous | FR-5, AC-1–AC-2, AC-6 |
| Harness cannot seed/control live tree | Stuck without Path B | Path B, FR-5 |
| Scope expands into fixture redesign | Dilutes 3-SP optional hardening | Exclusions, NFR-5 |
| Flaky or unbounded agent e2e | CI noise / hangs | NFR-2, AC-3 |
| Breaking unrelated e2e or fixture tests | False CI failures | FR-6, AC-4 |

## Q&A

- **Q: Why is this needed if PYPOST-942 already tested tree negatives?**
  **A:** Fixture tests lock the agent API on synthetic controls. This debt asks
  for live product collection-tree confidence under agent e2e, or an explicit
  deferral.
- **Q: Is documented deferral really Done?**
  **A:** Yes. Jira acceptance allows documented deferral when harness gaps
  prevent a live proof.
- **Q: Must both missing-label and out-of-range be proven live?**
  **A:** Preferred. If the harness can only host one safely, prove that one and
  document the residual gap (FR-3).
- **Q: Should production select behaviour change?**
  **A:** Not expected. Coverage or deferral only unless a live proof finds a
  real defect.
- **Q: Does this replace fixture negative tests?**
  **A:** No. Fixture coverage remains the baseline contract (FR-6, AC-4).
- **Q: Is combo or list-view negative select in scope?**
  **A:** No — owned by PYPOST-974 and related item-view tickets.
- **Q: Jira / commit in this run?**
  **A:** No — parent orchestrator owns later phases.
