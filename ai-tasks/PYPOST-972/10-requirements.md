# PYPOST-972: Dedicated item view has no model test

## Goals

PYPOST-939 added model-backed list selection to the agent `ui_select` capability.
Happy-path text and index selection for a plain list view are covered, and the
missing-model failure is documented for callers. A dedicated automated proof
that selecting a model-backed item view with no attached model fails with the
established public error is still missing.

The business goal is to lock that error contract in CI so a regression cannot
silently change how harness authors learn that a list view is not ready to
select. Maintainers gain an early, actionable signal; agent and e2e authors keep
the same clear failure they already rely on when a model is absent.

This is the Low-priority, 1-story-point Debt follow-up recorded as TD-2 in
PYPOST-939. Labels: `agent`, `tech-debt`, `testing`.

## Programming Language

Python with PySide6. Task artifacts and developer documentation use English
Markdown.

## User Stories

- As a **maintainer**, I want a dedicated automated check that a model-backed
  item view without a model fails with the established public error, so that
  regression is caught before release.
- As an **agent or e2e author**, I want selecting an unready list view to keep
  raising a clear, interactable-target failure naming the missing-model
  condition, so drive scripts remain diagnosable.
- As a **CI owner**, I want the error-path proof to stay green under explicit
  timeouts in the offscreen Qt suite, so confidence does not depend on manual
  inspection.
- As a **failure-triage owner**, I want the item-view missing-model reason to
  remain distinct from the tree missing-model reason, so logs identify which
  control family was unready.

## Definition of Done

- A dedicated automated error-path proof covers selecting a `QListView` (or
  equivalent flat model-backed item view) that has no model attached.
- The proof asserts the established interactable-target failure with the public
  reason text `item view has no model`.
- The error-path test is green in the focused automated suite with explicit
  timeout protection.
- Existing happy-path and other negative `ui_select` coverage remains green and
  unchanged in meaning.
- No production UI, public API, logging, or metric behavior changes.
- Unticketed follow-ups, if any, live only in this task’s `60-tech-debt.md`.

## Task Description

### Problem

PYPOST-939 documented and implemented a missing-model failure for model-backed
item views, but left dedicated automated coverage as optional Low debt (TD-2).
Success paths for list-view text and index selection are already covered.
Without a dedicated negative-path proof, the public missing-model contract can
regress without a CI signal.

### Business Reason

Harness authors and CI investigators need a stable, test-backed failure when a
named list view is present but not selectable because it has no model. Locking
that contract reduces triage time and prevents silent drift of a documented
troubleshooting outcome.

### In Scope

- Add dedicated automated coverage for the item-view missing-model error path.
- Assert the established public exception boundary and reason text for that
  path.
- Keep the proof in the established offscreen Qt / fixture style with explicit
  timeouts.
- Preserve existing select success and other select failure contracts.

### Exclusions

- Changing production widgets, identities, or product UI.
- Changing the wording or type of the established missing-model error (unless a
  test reveals a real defect — then the fix belongs in later steps).
- Adding new select capabilities or widget types.
- Expanding coverage to unrelated negative paths (missing option, out-of-range
  index) already owned elsewhere.
- Requiring a live product `QListView` agent e2e scenario (none exists today).
- Broad suite redesign or unrelated cleanup.

## Functional Requirements

- **FR-1:** Selecting a named model-backed item view (`QListView` or equivalent
  flat item view) that has no model must fail at the public `ui_select`
  boundary.
- **FR-2:** The failure must be the established interactable-target error with
  the public reason `item view has no model`.
- **FR-3:** A dedicated automated proof must exercise that path and remain
  green.
- **FR-4:** The item-view missing-model reason must remain distinct from the
  tree missing-model reason.
- **FR-5:** Existing list-view text/index success paths and other select error
  paths must retain their current meaning and stay green.
- **FR-6:** Developer troubleshooting guidance that documents
  `item view has no model` must remain accurate.

## Non-Functional Requirements

- **NFR-1 — Compatibility:** Behavior-preserving for callers; no new public API
  surface.
- **NFR-2 — Stability:** Offscreen, deterministic Qt fixture execution with
  explicit pytest timeouts; no live network.
- **NFR-3 — Maintainability:** One focused error-path proof that mirrors the
  established missing-model contract already used by trees in production
  behavior.
- **NFR-4 — Observability:** No new log or metric requirements; do not expand
  captured model payloads.
- **NFR-5 — Scope control:** Test-debt only unless a proven defect forces a
  minimal behavior fix.

## Acceptance Criteria

- **AC-1:** Dedicated error-path coverage exists for a `QListView` (or flat
  model-backed item view) with no model.
- **AC-2:** The proof asserts `UiTargetNotInteractableError` whose message
  includes `item view has no model`.
- **AC-3:** The error-path test is green under explicit timeout protection.
- **AC-4:** Existing `ui_select` happy-path and other negative-path coverage
  remains green.
- **AC-5:** No user-visible product behavior, public interface, logging schema,
  or metric changes.
- **AC-6:** Canonical troubleshooting docs remain consistent with the locked
  error reason.

## Constraints and Assumptions

- Source debt: PYPOST-939 TD-2 — “Dedicated `item view has no model` test;
  Mirror tree no-model coverage.”
- “Mirror tree” means the same public failure family and a distinct reason
  string already used for trees (`tree has no model`), not a claim that a
  dedicated tree no-model automated test already exists in the suite today.
- The missing-model behavior for item views is the accepted baseline from
  PYPOST-939; this task primarily locks it with a test.
- Happy-path `QListView` text/index selection remains covered by existing
  PYPOST-939 tests.
- Missing-option and out-of-range index debt is owned by other tickets
  (including PYPOST-942 and related follow-ups), not this one.
- Step 1 is documentation-only and remains pending review.

## Main Entities and Interactions

| Entity | Business role | Required outcome |
| --- | --- | --- |
| Agent or e2e caller | Requests select on a named control | Gets a clear missing-model failure |
| Model-backed item view | List control without an attached model | Remains unselectable |
| Public select boundary | Maps invalid ready-state to agent error | Raises interactable error |
| Missing-model reason | Distinguishes item-view unreadiness | Contains `item view has no model` |
| Tree missing-model reason | Parallel contract for trees | Remains distinct (`tree has no model`) |
| CI error-path proof | Guards the contract | Stays green under timeouts |

Interaction overview:

1. A caller names a supported model-backed item view and requests selection.
2. The control is present but has no model attached.
3. Selection fails at the public boundary with the established missing-model
   reason.
4. CI proves that failure path and keeps sibling select contracts green.

## Evidence and Traceability

| Evidence | Current observation | Requirement impact |
| --- | --- | --- |
| PYPOST-939 TD-2 | Records Low debt for dedicated missing-model test | Goals, AC-1 |
| Jira PYPOST-972 | Acceptance: error-path test green | AC-2, AC-3 |
| Item-view select path | Raises `item view has no model` when model absent | FR-1, FR-2 |
| Tree select path | Raises distinct `tree has no model` | FR-4 |
| Existing ui_select tests | List-view success covered; no dedicated no-model case | FR-3, FR-5 |
| `doc/dev/ui_actions.md` | Documents `item view has no model` troubleshooting | FR-6 |
| Suite search | No automated assertion currently matches `has no model` | Issue below |

## Risks

| Risk | Consequence | Requirement guard |
| --- | --- | --- |
| Error wording is “improved” during the task | Callers and docs drift | FR-2, AC-5 |
| Tree and item-view reasons are merged | Triage loses control-family signal | FR-4 |
| Scope expands into other negative paths | Dilutes 1-SP debt focus | Exclusions, NFR-5 |
| Proof depends on live product widgets | Flaky or impossible coverage | In scope fixture style |
| Tree no-model gap is silently assumed covered | False parity expectation | Constraints, Q&A |

## Issues Found

- **Tree no-model automated coverage is also absent.** TD-2 says “mirror tree
  no-model coverage,” but the suite currently has no dedicated assertion for
  `tree has no model` either. Production code and item-view docs establish the
  contract; only the item-view dedicated test is in scope for PYPOST-972.
  Expanding to a tree no-model proof would be separate follow-up debt if desired.

## Q&A

- **Q: Why add a test if the error already exists?**
  **A:** Happy paths are covered; the documented missing-model failure is not.
  Without a dedicated proof, CI cannot detect a silent contract regression.
- **Q: Does “mirror tree no-model coverage” require changing tree tests?**
  **A:** No. It means keep the same failure family and a distinct reason string.
  A dedicated tree no-model test is not part of this ticket’s acceptance.
- **Q: Should the task change the error message?**
  **A:** No. Lock the established public reason unless a real defect is proven.
- **Q: Is a live product list-view e2e required?**
  **A:** No. PYPOST-939 accepted that no product list-view id exists today;
  fixture coverage is sufficient.
- **Q: Does this change selection success behavior?**
  **A:** No. It is test debt for an existing error path.
