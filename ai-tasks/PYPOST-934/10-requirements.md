# PYPOST-934: Agent e2e timeout companion for dialog settle step diagnostics

## Goals

[PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) delivered happy-path
`agent_e2e` coverage that opens Settings, waits for the product dialog to
appear, and rewraps timeout failures with a stable step name and modal context
scalars. That failure-path diagnosability is **implemented** in the rewrap logic
but **not asserted** by automated coverage — the optional timeout companion was
deferred when a second full agent session after the modal path segfaulted
locally.

Without a dedicated timeout companion, regressions in dialog-settle failure
diagnostics (missing step, missing modal context) can slip through CI while the
happy path stays green. Maintainers and agents then lose actionable context when
Settings dialog settle fails in automation — the same gap the golden Send flow
already closes with its forced-settle timeout companion.

**Business why:** Lock in FR3-style diagnosability for product dialog settle
under `agent_e2e`, matching the confidence level already established for golden
Send response settle timeouts.

Source: [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919)
`60-tech-debt.md` TD-1 (Medium). Parent story:
[PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919). Browse:
[PYPOST-934](https://pypost.atlassian.net/browse/PYPOST-934).

## Programming Language

Python (`.cursor/lsr/do-python.md`). Automated coverage under the project’s
`agent_e2e` harness path. Task artifacts in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **maintainer**, I want an `agent_e2e` companion that forces dialog-settle
  timeout and asserts failure diagnostics, so regressions in step naming or
  modal context are caught in CI — not only when someone manually triggers a
  failure.
- As an **AI agent / harness author**, I want dialog-settle timeouts to carry a
  stable step identifier (`wait_dialog_after_settings_open`) and modal state
  scalars, so automation logs and CI failures clearly identify the dialog-settle
  step and what modal (if any) was active.
- As a **CI / headless runner**, I want the companion to finish under a bounded
  wall-clock budget and not hang the job when the forced timeout path runs.
- As a **sibling story owner** (PYPOST-919 dialog settle), I want this companion
  to extend the existing dialog-settle proof without replacing or weakening the
  happy-path scenario or the Send golden timeout companion pattern.

## Definition of Done

- An `agent_e2e`-marked **timeout companion** exists alongside the PYPOST-919
  dialog-settle coverage (same module family as the happy-path proof).
- The companion **forces** dialog-settle failure within a near-zero budget (same
  intent as the golden Send timeout companion precedent).
- On forced timeout, assertions verify:
  - `diagnostics["step"] == "wait_dialog_after_settings_open"`
  - Modal diagnostic scalars are present (at minimum `dialog_title` and
    `active_modal_type` as established by PYPOST-919 observability).
- The full `agent_e2e` suite stays green under `make test-agent-e2e`.
- The existing happy-path dialog-settle test remains valid and passing.
- Unticketed follow-ups (if any) are recorded only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

Acceptance (from Jira): **Companion test asserts diagnostics step + modal
scalars; suite stays green under `make test-agent-e2e`.**

## Task Description

**Problem:** PYPOST-919 ships dialog-settle timeout rewrap with step
`wait_dialog_after_settings_open` and modal scalars (`dialog_title`,
`active_modal_type`), but only the happy path is regression-tested. Failure
diagnostics can regress silently.

**Business need:** Automated proof that dialog-settle timeouts remain
diagnosable — parity with the golden Send forced-timeout companion — without
introducing CI hangs or destabilizing the existing happy-path proof.

### In Scope

- One `agent_e2e` timeout companion for the Settings dialog-settle scenario
  delivered in PYPOST-919.
- Forced near-zero settle budget on the dialog-settle wait so timeout occurs
  deterministically.
- Assertions on timeout failure diagnostics: step name and modal scalars.
- Bounded execution suitable for standard `make test-agent-e2e` selection.
- Preference for same-process / single-session execution when a second full
  agent session after the modal path is known to segfault locally (constraint
  from parent Step 4 — not a hard blocker if a safe alternative exists).

### Out of Scope

- Changing production dialog-settle or wait APIs (test-only debt).
- Replacing or duplicating the PYPOST-919 happy-path dialog-settle proof.
- Full Settings functional testing or full product dialog matrix.
- Golden Send → response flow changes (separate timeout companion already
  exists).
- `SETTINGS_DIALOG` widget identity (PYPOST-935 / PYPOST-919 TD-2).
- Shared modal settle helper extraction (PYPOST-936 / PYPOST-919 TD-3).
- Migrating Settings from modal `exec()` to async `open()` — product change.
- Broader agent-e2e packaging / `make` redesign.
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: Timeout companion coverage exists under `@pytest.mark.agent_e2e` for the
  Settings dialog-settle scenario (sibling to the PYPOST-919 happy-path test).
- FR2: The companion forces dialog-settle timeout within a near-zero budget so
  failure is deterministic (not dependent on ambient timing flakiness).
- FR3: On forced timeout, failure diagnostics include the stable dialog-settle
  step identifier from the parent observability contract.
- FR4: On forced timeout, failure diagnostics include modal context scalars from
  the parent observability contract (minimal modal state — title and active modal
  type; no full widget trees or dialog field dumps).
- FR5: The companion completes without hanging CI under the module’s wall-clock
  timeout budget.
- FR6: Existing happy-path dialog-settle test and golden Send coverage remain
  passing and unchanged in acceptance meaning.
- FR7: Failure-path diagnosability for dialog settle matches the intent of the
  golden Send timeout companion (step + context scalars on forced timeout).

## Non-Functional Requirements

- **Boundedness:** Forced timeout path must not hang CI; module-level timeout
  markers remain mandatory per project testing rules.
- **CI suitability:** Runs under offscreen / standard `make test-agent-e2e`
  selection alongside existing dialog-settle coverage.
- **Stability:** Prefer same-process execution when multi-session after modal
  is known to segfault; companion must not destabilize the suite.
- **Minimalism:** One focused timeout companion; not a full dialog failure
  matrix.
- **No production → tests imports:** Production agent code must not import from
  `tests/`.
- **English docs;** line length ≤ 100 where practical.

## Constraints and Assumptions

- Programming language: Python.
- Parent / source debt: PYPOST-919 TD-1 (Medium); inherits dialog-settle step
  name and modal scalar contract from PYPOST-919 observability.
- Reference pattern: golden Send timeout companion precedent — business parity
  for failure-path diagnosability, not a mandate to copy implementation
  structure verbatim.
- Parent observability contract (PYPOST-919): dialog-settle step name
  `wait_dialog_after_settings_open` and modal scalars on timeout rewrap.
- Known risk: second full `agent_e2e_session` after modal path segfaulted during
  PYPOST-919 Step 4; Qt/PySide segfault infrastructure tracked under
  [PYPOST-429](https://pypost.atlassian.net/browse/PYPOST-429) lineage.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval gate / no Jira updates in this step).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Timeout companion | Automated proof that forced dialog-settle failure is diagnosable |
| Dialog-settle step | Stable failure identifier: `wait_dialog_after_settings_open` |
| Modal diagnostic scalars | `dialog_title`, `active_modal_type` — modal state at timeout |
| Forced timeout | Near-zero settle budget to trigger failure deterministically |
| Happy-path dialog settle | PYPOST-919 proof that Settings open → wait → dismiss succeeds |
| Golden Send timeout companion | Precedent for step + context scalar assertions on forced timeout |
| CI / agent_e2e runner | Runs suite under bounded budget; must not hang |

Interaction overview:

1. Harness reaches UI ready (same session family as happy-path dialog settle).
2. Companion drives Settings open and forces dialog-settle timeout (near-zero
   budget).
3. Timeout raises `UiWaitTimeoutError` with rewrapped diagnostics.
4. Companion asserts step name and modal scalars match the PYPOST-919 contract.
5. Harness completes cleanup without hanging CI.
6. Happy-path dialog-settle and golden Send proofs remain separate green checks.

## Q&A

- Q: Why is this separate from PYPOST-919 if the rewrap already exists?
  A: PYPOST-919 acceptance was happy-path dialog settle; timeout diagnostics
  were implemented but deferred from automated assertion (TD-1). This ticket
  closes that coverage gap.

- Q: Must the companion use a second full agent session?
  A: Prefer same-process / no second full session if multi-session after modal
  still segfaults. A safe single-session approach satisfies acceptance.

- Q: Which modal scalars must be asserted?
  A: At minimum `dialog_title` and `active_modal_type` — the scalars the parent
  observability contract documents on the timeout rewrap path.

- Q: Does this change production behavior?
  A: No. This is test-only debt asserting existing failure diagnostics; no new
  production API or log streams are required for acceptance.

- Q: What if forcing timeout is flaky?
  A: Near-zero budget (same intent as golden Send companion) should make timeout
  deterministic; module wall-clock timeout guards against hangs.

- Q: Jira / commit in this run?
  A: No — parent orchestrator owns Phase D/F.
