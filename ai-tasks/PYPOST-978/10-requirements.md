# PYPOST-978: Migrate golden e2e to tab-scoped session wait

## Goals

[PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949) delivered
tab-scoped session waits so agent and harness authors can wait for text under
the active request tab with the same scoping contract as UI actions. The golden
agent e2e path still settles via free-function wait helpers instead of that
session API.

**Business why:** Golden e2e authors and maintainers should use the same
tab-scoped session wait contract as the rest of the agent harness. Migrating
reduces reliance on free-function wait imports, keeps golden settle aligned with
the preferred session API, and must leave golden Send → response behaviour
unchanged for CI confidence.

This is the Low-priority, 1-story-point Debt follow-up recorded as TD-1 in
[PYPOST-949/60-tech-debt.md](../PYPOST-949/60-tech-debt.md). Labels: `agent`,
`e2e`, `tech-debt`. Browse:
[PYPOST-978](https://pypost.atlassian.net/browse/PYPOST-978).

## Programming Language

Python (`.cursor/lsr/do-python.md`). Task artifacts and any developer
documentation updates use English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **agent / golden e2e author**, I want golden Send settle to use the
  tab-scoped session text-wait API so golden scripts follow the same wait
  contract as other agent e2e flows.
- As a **harness maintainer**, I want fewer free-function wait imports in the
  golden path so the preferred session wait surface is the default example.
- As a **regression owner**, I want golden behaviour (observed settle outcomes
  and pass/fail meaning) unchanged so CI confidence is not weakened by this
  debt cleanup.
- As a **CI owner**, I want any touched golden / agent e2e proofs to remain
  green under the established agent e2e path with explicit timeouts.

## Definition of Done

- Golden agent e2e Send settle uses the tab-scoped session text-wait API
  (`wait_for_text` with current-tab scoping) instead of free-function wait
  helpers for that settle path.
- Golden behaviour is unchanged: same observed settle outcomes and pass/fail
  meaning for authors and CI.
- Free-function wait imports on the migrated golden path are reduced (no longer
  required solely for that settle).
- Existing unrelated agent e2e and wait coverage remains green and unchanged in
  meaning.
- No user-facing product behaviour, public product API, logging schema, or
  metric changes.
- Unticketed follow-ups, if any, live only in this task’s `60-tech-debt.md`.

## Task Description

### Problem

PYPOST-949 closed session-level tab-scoped waits and left golden migration as
optional cosmetic DRY. Golden still demonstrates settle via free-function wait
helpers, so the golden path is not the canonical example of the session wait
API authors are expected to prefer.

### Business Reason

Align golden e2e with the tab-scoped session wait contract so maintainers and
authors see one preferred wait style, with fewer free-function imports, without
changing what golden proves.

### In Scope

- Migrate golden agent e2e text waits used for Send → response settle to the
  tab-scoped session wait API.
- Preserve golden settle meaning and outcomes.
- Reduce free-function wait imports that exist only to support that settle.
- Keep proofs under the established agent e2e path with explicit timeouts.

### Exclusions

- Changing production UI, widget identities, or product behaviour.
- Redesigning wait primitives, adding new wait APIs, or changing default
  window-scoped session wait behaviour.
- Broad golden rewrite beyond settle-wait migration.
- Explicit tab-scoped `wait_for_widget` / `wait_for_enabled` coverage (owned by
  [PYPOST-979](https://pypost.atlassian.net/browse/PYPOST-979)).
- Golden timeout-diagnostics lock alignment (owned by
  [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950)).
- Jira ticket creation, commit, or status transitions (orchestrator).

## Functional Requirements

- **FR-1:** Golden Send → response settle must wait for the expected text via
  the session text-wait API with current-tab scoping enabled.
- **FR-2:** After migration, golden settle outcomes (success and failure meaning
  for authors/CI) must match pre-migration behaviour.
- **FR-3:** The migrated golden path must not require free-function text-wait
  imports solely for that settle.
- **FR-4:** Unrelated agent e2e scenarios and wait regression coverage must
  retain their current meaning and stay green.
- **FR-5:** Developer guidance that documents golden settle or session waits
  must remain accurate after the migration (update only if wording would
  otherwise be wrong).

## Non-Functional Requirements

- **NFR-1 — Compatibility:** Behaviour-preserving for golden and product
  callers; no new public product API.
- **NFR-2 — Stability:** Touched golden / agent e2e proofs remain deterministic
  under the offscreen agent e2e path, with explicit pytest timeouts.
- **NFR-3 — Maintainability:** Prefer a focused golden settle migration over
  broad harness cleanup.
- **NFR-4 — Observability:** No new log or metric requirements.
- **NFR-5 — Scope control:** Low-priority debt; limit changes to golden
  tab-scoped session wait adoption and necessary doc accuracy.

## Acceptance Criteria

- **AC-1:** Golden e2e uses tab-scoped session `wait_for_text` (current-tab
  scoping) for the Send settle path formerly served by free-function waits.
- **AC-2:** Golden behaviour is unchanged (settle outcomes and pass/fail meaning).
- **AC-3:** Free-function wait imports on that golden settle path are fewer
  than before (no longer required solely for settle).
- **AC-4:** Scoped agent e2e / golden proofs remain green with explicit timeout
  protection.
- **AC-5:** No user-visible product behaviour, public product interface, logging
  schema, or metric changes.
- **AC-6:** Closes PYPOST-949 TD-1 (optional golden migration to tab-scoped
  session wait).

## Constraints and Assumptions

- Source debt: PYPOST-949 TD-1 — optional golden migration to session
  `wait_for_text` with current-tab scoping.
- Session tab-scoped text wait already exists and is test-backed; this task
  adopts it in golden, it does not invent the wait contract.
- Jira acceptance: golden behaviour unchanged; fewer free-function imports.
- Sprint-task-runner batch: autonomous progression; no user approval gates in
  this subagent run.
- Parent PYPOST-949 is Done; this ticket closes the optional golden-alignment
  follow-up.

## Main Entities and Interactions

| Entity | Business role | Required outcome |
| --- | --- | --- |
| Golden agent e2e | Canonical Send → settle proof | Same behaviour; session wait style |
| Agent app session | Preferred wait surface | Tab-scoped text wait used by golden |
| Tab-scoped text wait | Wait under active request tab | Used for golden settle |
| Free-function wait helper | Legacy settle helper | No longer required for golden settle |
| Active request tab | Scope for multi-tab-safe waits | Settle targets current tab |
| CI / maintainers | Rely on golden meaning | Unchanged pass/fail contract |

Interaction overview:

1. Golden agent e2e performs Send and waits for response settle text.
2. Settle uses the session text-wait API with current-tab scoping.
3. Observed settle outcomes match the prior golden contract.
4. Free-function wait imports are no longer needed for that settle.
5. Unrelated agent e2e and wait proofs remain green.

## Evidence and Traceability

| Evidence | Current observation | Requirement impact |
| --- | --- | --- |
| PYPOST-949 TD-1 | Optional golden migration to session tab-scoped wait | Goals, AC-6 |
| PYPOST-949 DoD / out of scope | Golden rewrite not required in parent | Problem statement |
| Jira PYPOST-978 | Behaviour unchanged; fewer free-function imports | AC-2, AC-3 |
| PYPOST-979 | Tab-scoped widget/enabled tests | Exclusions |
| PYPOST-950 | Golden timeout-diagnostics alignment | Exclusions |

## Risks

| Risk | Consequence | Requirement guard |
| --- | --- | --- |
| Silent change to golden settle meaning | CI false confidence / noise | FR-2, AC-2 |
| Partial migration leaves dual wait styles | Debt not closed | FR-1, FR-3, AC-1, AC-3 |
| Scope expands into wait redesign | Dilutes 1-SP cosmetic debt | Exclusions, NFR-5 |
| Flaky or unbounded golden e2e | CI noise / hangs | NFR-2, AC-4 |
| Breaking unrelated wait / e2e tests | False CI failures | FR-4, AC-4 |

## Q&A

- **Q: Why migrate golden if free-function waits still work?**
  **A:** PYPOST-949 left golden on free-function helpers as optional DRY.
  Session tab-scoped waits are the preferred contract; golden should exemplify
  them without changing what it proves.
- **Q: Must golden behaviour change?**
  **A:** No. Acceptance requires unchanged golden behaviour (FR-2, AC-2).
- **Q: Is inventing a new wait API in scope?**
  **A:** No. Adopt the existing tab-scoped session text-wait contract only.
- **Q: Are widget/enabled tab-scoped proofs in scope?**
  **A:** No — owned by PYPOST-979.
- **Q: Is timeout-diagnostics lock work in scope?**
  **A:** No — owned by PYPOST-950.
- **Q: Jira / commit in this run?**
  **A:** No — parent orchestrator owns later phases.
