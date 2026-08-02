# PYPOST-979: Tab-scoped wait_for_widget / wait_for_enabled tests

## Goals

[PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949) delivered
session-level tab-scoped waits so harness authors can wait under the active
request tab with the same scoping contract as UI actions. Multi-tab regression
proof today covers tab-scoped text waits. Tab-scoped widget presence and
enabled-state waits share the same current-tab scoping contract but lack an
explicit multi-tab proof.

**Business why:** Agent and harness authors rely on tab-scoped
`wait_for_widget` and `wait_for_enabled` when settling readiness under the
active tab in multi-tab flows. Without an explicit multi-tab fixture proving
those waits see only the active tab (not duplicate role ids on background
tabs), the widget/enabled half of the tab-scoping contract can regress silently
even while text-wait proofs stay green.

This is the Low-priority, 2-story-point Debt follow-up recorded as TD-2 in
[PYPOST-949/60-tech-debt.md](../PYPOST-949/60-tech-debt.md). Labels: `agent`,
`tech-debt`, `testing`. Browse:
[PYPOST-979](https://pypost.atlassian.net/browse/PYPOST-979).

## Programming Language

Python (`.cursor/lsr/do-python.md`). Task artifacts and any developer
documentation updates use English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **agent / harness author**, I want automated proof that session
  `wait_for_widget` with current-tab scoping finds the widget under the active
  request tab only, so multi-tab readiness waits do not latch onto a background
  tab’s duplicate role id.
- As an **agent / harness author**, I want automated proof that session
  `wait_for_enabled` with current-tab scoping observes enabled state under the
  active request tab only, so enabled settle in multi-tab flows is trustworthy.
- As a **regression owner**, I want a multi-tab fixture that demonstrates
  widget/enabled waits are scoped to the active tab, so the tab-scoping
  contract for those waits cannot regress without a failing test.
- As a **CI owner**, I want the new proofs to run under the established agent /
  UI wait test path with explicit timeouts, without changing product behaviour
  or weakening existing wait coverage.

## Definition of Done

- Explicit automated coverage proves tab-scoped session `wait_for_widget`
  observes widgets under the active request tab in a multi-tab fixture.
- Explicit automated coverage proves tab-scoped session `wait_for_enabled`
  observes enabled state under the active request tab in a multi-tab fixture.
- The multi-tab fixture shows that widget/enabled waits with current-tab
  scoping are scoped to the active tab (not satisfied by background-tab
  duplicates alone).
- Existing unrelated agent e2e and wait coverage remains green and unchanged in
  meaning.
- No user-facing product behaviour, public product API, logging schema, or
  metric changes.
- Unticketed follow-ups, if any, live only in this task’s `60-tech-debt.md`.

## Task Description

### Problem

PYPOST-949 closed session-level tab-scoped waits for text, widget, and enabled
helpers, and left TD-2 for explicit multi-tab proofs of the widget and enabled
helpers. Text waits already have multi-tab regression coverage.
`wait_for_widget` and `wait_for_enabled` share the same current-tab scoping
contract but are not yet proven under a multi-tab fixture. Authors and
maintainers therefore lack a dedicated signal that those waits stay active-tab
safe.

[PYPOST-978](https://pypost.atlassian.net/browse/PYPOST-978) migrated golden
e2e to tab-scoped session text wait and deferred widget/enabled multi-tab
proofs to this ticket.

### Business Reason

Give harness authors and regression owners explicit confidence that
tab-scoped widget and enabled waits honour the active-tab contract in
multi-tab scenarios — the same assurance already present for tab-scoped text
waits — so readiness settle cannot silently match background tabs.

### In Scope

- Explicit tests for tab-scoped session `wait_for_widget` under a multi-tab
  fixture.
- Explicit tests for tab-scoped session `wait_for_enabled` under a multi-tab
  fixture.
- Proof that those waits with current-tab scoping are scoped to the active
  request tab.
- Keep proofs under the established agent / UI wait test path with explicit
  timeouts.
- Update developer guidance only if wording would otherwise be inaccurate
  after the proofs exist.

### Exclusions

- Changing production UI, widget identities, or product behaviour.
- Redesigning wait primitives, adding new wait APIs, or changing default
  window-scoped session wait behaviour.
- Expanding multi-tab text-wait coverage (already owned / covered by
  PYPOST-949).
- Golden e2e text-wait migration (owned by
  [PYPOST-978](https://pypost.atlassian.net/browse/PYPOST-978)).
- Golden timeout-diagnostics lock alignment (owned by
  [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950)).
- Making `wait_for_snapshot` tab-scoped (explicitly out of PYPOST-949 scope).
- Jira ticket creation, commit, or status transitions (orchestrator).

## Functional Requirements

- **FR-1:** The suite must include an explicit multi-tab proof for session
  `wait_for_widget` with current-tab scoping enabled.
- **FR-2:** The suite must include an explicit multi-tab proof for session
  `wait_for_enabled` with current-tab scoping enabled.
- **FR-3:** Those proofs must demonstrate that widget/enabled waits with
  current-tab scoping are satisfied only with respect to the active request
  tab (background-tab duplicates alone must not satisfy the active-tab wait).
- **FR-4:** Unrelated agent e2e scenarios and wait regression coverage must
  retain their current meaning and stay green.
- **FR-5:** Developer guidance that documents tab-scoped widget/enabled waits
  must remain accurate after the proofs land (update only if wording would
  otherwise be wrong).

## Non-Functional Requirements

- **NFR-1 — Compatibility:** Behaviour-preserving for product callers; no new
  public product API.
- **NFR-2 — Stability:** New proofs remain deterministic under the offscreen
  agent / UI wait test path, with explicit pytest timeouts.
- **NFR-3 — Maintainability:** Prefer focused multi-tab widget/enabled proofs
  over broad harness rewrite.
- **NFR-4 — Observability:** No new log or metric requirements.
- **NFR-5 — Scope control:** Low-priority debt; limit changes to explicit
  tab-scoped widget/enabled multi-tab proofs and necessary doc accuracy.

## Acceptance Criteria

- **AC-1:** Multi-tab fixture proves session `wait_for_widget` with
  current-tab scoping is scoped to the active request tab.
- **AC-2:** Multi-tab fixture proves session `wait_for_enabled` with
  current-tab scoping is scoped to the active request tab.
- **AC-3:** Background-tab widgets with the same role ids alone do not
  satisfy the active-tab widget/enabled waits under current-tab scoping.
- **AC-4:** Scoped agent / UI wait proofs remain green with explicit timeout
  protection.
- **AC-5:** No user-visible product behaviour, public product interface,
  logging schema, or metric changes.
- **AC-6:** Closes PYPOST-949 TD-2 (explicit tests for tab-scoped
  `wait_for_widget` / `wait_for_enabled`).

## Constraints and Assumptions

- Source debt: PYPOST-949 TD-2 — explicit tests for tab-scoped
  `wait_for_widget` / `wait_for_enabled`; acceptance is a multi-tab fixture
  proving widget/enabled scoped to the active tab.
- Session tab-scoped widget and enabled waits already exist; this task proves
  them under multi-tab conditions, it does not invent the wait contract.
- Tab-scoped text waits already have multi-tab coverage; this task does not
  re-prove text waits.
- Developer docs already describe optional current-tab scoping for
  `wait_for_widget` / `wait_for_enabled` (`doc/dev/ui_wait.md`).
- Sprint-task-runner batch: autonomous progression; no user approval gates in
  this subagent run.
- Parent PYPOST-949 is Done; this ticket closes the widget/enabled multi-tab
  proof follow-up.

## Main Entities and Interactions

| Entity | Business role | Required outcome |
| --- | --- | --- |
| Multi-tab fixture | Sets up active + background request tabs | Proves active-tab-only waits |
| Tab-scoped widget wait | Wait until widget exists under scope | Proven under active tab |
| Tab-scoped enabled wait | Wait until widget is enabled under scope | Proven under active tab |
| Active request tab | Scope for multi-tab-safe waits | Widget/enabled waits target it |
| Background request tab | Holds duplicate role ids | Must not alone satisfy active-tab wait |
| Agent app session | Preferred wait surface | Tab-scoped widget/enabled used in proofs |
| CI / maintainers | Rely on wait contract | Explicit regression signal |

Interaction overview:

1. Multi-tab fixture presents an active request tab and at least one background
   tab with overlapping role ids.
2. Session `wait_for_widget` with current-tab scoping targets the active tab.
3. Session `wait_for_enabled` with current-tab scoping targets the active tab.
4. Background-tab duplicates alone do not satisfy those active-tab waits.
5. Unrelated agent e2e and wait proofs remain green.

## Evidence and Traceability

| Evidence | Current observation | Requirement impact |
| --- | --- | --- |
| PYPOST-949 TD-2 | Explicit widget/enabled multi-tab tests deferred | Goals, AC-6 |
| PYPOST-949 missing tests | Widget/enabled tab-scope not explicitly covered | Problem statement |
| Jira PYPOST-979 | Multi-tab fixture proves widget/enabled scoped to active tab | AC-1, AC-2, AC-3 |
| PYPOST-978 | Golden text-wait migration; deferred widget/enabled proofs here | Exclusions, Goals |
| `doc/dev/ui_wait.md` | Documents optional current-tab scoping for widget/enabled | FR-5 |

## Risks

| Risk | Consequence | Requirement guard |
| --- | --- | --- |
| Proofs cover text waits again, not widget/enabled | TD-2 remains open in spirit | FR-1, FR-2, AC-1, AC-2 |
| Proofs do not show background-tab isolation | False confidence on scoping | FR-3, AC-3 |
| Scope expands into wait redesign | Dilutes 2-SP debt | Exclusions, NFR-5 |
| Flaky or unbounded new tests | CI noise / hangs | NFR-2, AC-4 |
| Breaking unrelated wait / e2e tests | False CI failures | FR-4, AC-4 |

## Q&A

- **Q: Why add tests if PYPOST-949 already shipped tab-scoped widget/enabled?**
  **A:** Parent covered text waits with a multi-tab proof and noted
  widget/enabled as low-risk unproven. Authors still need an explicit
  regression signal for those waits (TD-2).
- **Q: Must product wait behaviour change?**
  **A:** No. This task proves the existing tab-scoping contract; product
  behaviour and public APIs stay unchanged (AC-5).
- **Q: Are text-wait multi-tab proofs in scope?**
  **A:** No — already delivered by PYPOST-949; this ticket owns widget and
  enabled only.
- **Q: Is inventing a new wait API in scope?**
  **A:** No. Prove the existing tab-scoped session widget/enabled contract.
- **Q: Is golden e2e work in scope?**
  **A:** No — owned by PYPOST-978 (text) and PYPOST-950 (timeout diagnostics).
- **Q: Jira / commit in this run?**
  **A:** No — parent orchestrator owns later phases.
