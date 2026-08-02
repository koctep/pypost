# PYPOST-974: Combo out-of-range index contract test

## Goals

Agent and golden-flow authors use `ui_select` to choose options in combo boxes,
lists, and trees. When they pass an index outside the control’s valid range, they
need a clear, actionable failure — not silent mis-selection or ambiguous errors.

[PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) added dedicated
automated negative-path coverage for list and tree out-of-range indices. Combo
boxes already fail clearly for invalid indices in production, and a dedicated
missing-option test exists, but there is still no automated contract proof for
combo out-of-range indices. That gap leaves the only select control type without
matching index-boundary coverage in CI.

The business goal is parity across select control types so harness authors and
maintainers can trust that invalid combo indices are caught before release. This
is the Low-priority, 2-story-point Debt follow-up recorded as TD-1 in
[PYPOST-942/60-tech-debt.md](../PYPOST-942/60-tech-debt.md). Labels:
`tech-debt`, `testing`.

## Programming Language

Python with PySide6. Task artifacts and developer documentation use English
Markdown.

## User Stories

- As an **agent / e2e author**, I want an out-of-range combo index to fail with
  an explicit out-of-range error so bad indices do not slip through drive
  scripts or CI.
- As a **maintainer**, I want combo index-boundary failures locked by automated
  tests mirroring list and tree out-of-range coverage so regressions are caught
  before release.
- As a **CI owner**, I want the combo out-of-range error contract in the
  established offscreen Qt fixture suite with explicit timeouts so the proof
  stays green on every run.
- As a **failure-triage owner**, I want combo, list, and tree index errors to
  share the same actionable failure pattern so logs are consistent across control
  types.

## Definition of Done

- Automated tests assert a clear, actionable error when a combo select index is
  negative or beyond the last item.
- Invalid combo index cases are covered by at least one dedicated automated
  proof (including boundary values such as one below zero and one at or beyond
  the item count).
- Existing combo, list, and tree happy-path and other negative select tests
  remain passing and unchanged in meaning.
- No production UI, public API, logging, or metric behavior changes unless a
  test reveals a real defect (then fix belongs in later steps).
- Unticketed follow-ups, if any, live only in this task’s `60-tech-debt.md`.

## Task Description

### Problem

The agent select capability supports combo boxes by display text and by
zero-based index. Fixture tests prove successful combo selection and a dedicated
missing-option failure. List and tree already have dedicated out-of-range index
contract tests added in PYPOST-942. Combo out-of-range index behaviour is
implemented but not covered by a matching dedicated automated proof, so the
error contract could regress without CI signal.

### Business Reason

Consistent, test-backed failure messages across all select control types let
harness authors trust the agent API and diagnose bad indices quickly from CI
logs. Closing the combo gap completes the negative-path parity started in
PYPOST-942.

### In Scope

- Add dedicated automated negative-path coverage for combo select with invalid
  indices (negative and at or beyond item count).
- Assert the established actionable out-of-range failure pattern already used
  for list and tree index errors.
- Keep proofs in the established offscreen Qt fixture style with explicit
  timeouts.
- Preserve existing select success and other select failure contracts.

### Exclusions

- Changing production widgets, widget identities, or product UI.
- Altering select behaviour or error message wording (unless a test reveals a
  bug — then fix belongs in later steps).
- List, tree, or item-view negative paths (already owned by PYPOST-942,
  PYPOST-939, and related tickets).
- Live product combo agent e2e scenarios beyond the existing fixture suite.
- Broad suite redesign or unrelated cleanup.
- Jira ticket creation, commit, or status transitions (orchestrator).

## Functional Requirements

- **FR-1:** A combo select with index less than zero must fail at the public
  `ui_select` boundary with an actionable error indicating the index is out of
  range.
- **FR-2:** A combo select with index equal to or greater than the number of
  combo items must fail with the same out-of-range error pattern.
- **FR-3:** At least one dedicated automated proof must cover both invalid index
  boundary cases for combo selection.
- **FR-4:** The combo out-of-range failure must use the same actionable error
  pattern as list and tree out-of-range index failures (`option index out of
  range` style messaging).
- **FR-5:** Existing combo missing-option, list, tree, and happy-path select
  tests must retain their current meaning and stay green.
- **FR-6:** Developer troubleshooting guidance that documents select index errors
  must remain accurate once this debt is closed.

## Non-Functional Requirements

- **NFR-1 — Compatibility:** Behaviour-preserving for callers; no new public
  API surface unless a proven defect forces a minimal fix.
- **NFR-2 — Stability:** Offscreen, deterministic Qt fixture execution with
  explicit pytest timeouts; no live network.
- **NFR-3 — Maintainability:** Focused error-path proof mirroring the list/tree
  out-of-range contract tests from PYPOST-942.
- **NFR-4 — Observability:** No new log or metric requirements.
- **NFR-5 — Scope control:** Test-debt only; keep changes limited to combo
  out-of-range index coverage.

## Acceptance Criteria

- **AC-1:** Dedicated automated proof covers combo select with a negative index
  and asserts a clear out-of-range failure.
- **AC-2:** Dedicated automated proof covers combo select with an index at or
  beyond the item count and asserts the same out-of-range failure pattern.
- **AC-3:** Invalid index cases are exercised through one or more focused proofs
  (boundary parametrization acceptable).
- **AC-4:** Focused `ui_select` fixture tests stay green under explicit timeout
  protection with no change to existing happy-path or other negative contracts.
- **AC-5:** No user-visible product behaviour, public interface, logging schema,
  or metric changes unless a proven defect is found.
- **AC-6:** Closes PYPOST-942 TD-1 (combo out-of-range index contract test).

## Constraints and Assumptions

- Source debt: PYPOST-942 TD-1 — combo out-of-range index contract test.
- Combo out-of-range error behaviour already exists in production; this task
  adds test coverage, not new product behaviour.
- Standard fixture combo has three items (indices 0–2); boundary invalid indices
  are one below zero and one equal to the item count.
- Sprint-task-runner batch: autonomous progression; no user approval gates in
  this subagent run.
- Parent PYPOST-942 is closed; this ticket completes the optional parity gap
  noted in its tech-debt follow-ups.

## Main Entities and Interactions

| Entity | Business role | Required outcome |
| --- | --- | --- |
| Agent / harness | Drives named UI after ready | Gets clear failure on bad index |
| Select action | Chooses one option on a named control | Rejects invalid combo index |
| Combo control | Dropdown with enumerated items | Index must be within item count |
| Index | Zero-based position in the combo | Valid range enforced |
| Actionable error | Clear failure the author can fix | Out-of-range message in CI |
| CI / maintainers | Rely on contract tests | Combo parity with list/tree |

Interaction overview:

1. A harness calls select on a named combo with an invalid index.
2. The agent API rejects the call with an actionable out-of-range error.
3. Automated proof asserts that failure and stays green under timeout protection.
4. Existing list/tree out-of-range and combo happy-path tests remain green.

## Evidence and Traceability

| Evidence | Current observation | Requirement impact |
| --- | --- | --- |
| PYPOST-942 TD-1 | Records Low debt for combo out-of-range test | Goals, AC-6 |
| PYPOST-942 DoD | List/tree out-of-range tests delivered | FR-3, FR-4 parity target |
| Jira PYPOST-974 | Acceptance: parametrized invalid combo indices | AC-1–AC-3 |
| Existing combo missing-option test | Covers unknown label only | Gap for index path |
| List/tree out-of-range tests | Parametrized boundary coverage | FR-3, NFR-3 model |

## Risks

| Risk | Consequence | Requirement guard |
| --- | --- | --- |
| Combo index gap persists | Regressions undetected | FR-1–FR-3, AC-1–AC-3 |
| Inconsistent error pattern | Harder triage across controls | FR-4 |
| Scope creep into production | Dilutes 2-SP debt task | Exclusions, NFR-5 |
| Breaking unrelated select tests | False CI failures | FR-5, AC-4 |

## Q&A

- **Q: Why tests only — no code change expected?**
  **A:** Combo out-of-range errors are already implemented; TD-1 tracks missing
  dedicated automated proof, mirroring PYPOST-942’s list/tree approach.
- **Q: Why mirror list/tree coverage?**
  **A:** PYPOST-942 established negative-path parity for list and tree; combo
  is the remaining select type without out-of-range index contract tests.
- **Q: Does combo missing-option coverage satisfy this?**
  **A:** No. Missing display text and invalid index are separate failure paths;
  only the label path is tested today.
- **Q: Must error strings match list/tree exactly?**
  **A:** Same actionable pattern (`option index out of range`); exact wording
  follows the established production contract.
- **Q: Include nested tree or item-view index errors?**
  **A:** Out of scope — owned by PYPOST-942, PYPOST-939, and related tickets.
- **Q: Jira / commit in this run?**
  **A:** No — parent orchestrator owns later phases.
