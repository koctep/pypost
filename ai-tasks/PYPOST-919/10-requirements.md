# PYPOST-919: Product dialog settle coverage in golden flow

## Goals

AI agents and automated harnesses already have settle/wait helpers
([PYPOST-837](https://pypost.atlassian.net/browse/PYPOST-837)) and a golden
Send → response proof
([PYPOST-838](https://pypost.atlassian.net/browse/PYPOST-838)). Those waits are
proven against synthetic delayed widgets and against the response panel after
Send — **not** against a real product dialog appearing after a user action.

Without that coverage, agents can still race when opening Settings (or similar
product dialogs): the harness may continue before the dialog is present, or
maintainers may assume dialog settle is covered when it is not.

This debt closes that gap: **golden or agent_e2e coverage must wait for a
product dialog to appear after an action**, so settle behavior is proven on a
real product surface.

Source: [PYPOST-852](https://pypost.atlassian.net/browse/PYPOST-852) TD-1
(originally noted under PYPOST-837 TD-3 and PYPOST-838 missing-tests).

## Programming Language

Python (`.cursor/lsr/do-python.md`). Automated coverage under the project’s
`agent_e2e` / golden harness path. Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **AI agent** (or test harness), I want to open a product dialog via a
  normal UI action and wait until that dialog is present before continuing, so
  I do not race dialog creation.
- As a **maintainer**, I want golden or `agent_e2e` coverage that exercises
  “action → wait for product dialog appears,” so regressions in dialog settle
  are caught in CI — not only synthetic fixture waits.
- As a **sibling story owner** (settle helpers / golden flow), I want this proof
  to reuse existing wait and agent/harness capabilities rather than inventing a
  parallel wait stack.
- As a **CI / headless runner**, I want the scenario to finish under a bounded
  timeout in the offscreen GUI environment so a stuck or missing dialog fails
  clearly instead of hanging the job.

## Definition of Done

- Golden and/or `agent_e2e`-marked coverage performs a product UI action that
  causes a **product dialog** to appear, then **waits** until that dialog is
  present (settled) before further assertions or cleanup.
- The wait uses the shared settle/wait capability already delivered for agents
  (not a one-off sleep).
- On timeout or failure, diagnostics are actionable enough to see that the
  dialog settle step failed (step/context identifiable).
- The scenario runs under the project’s standard offscreen / `agent_e2e`
  workflow with a bounded wall-clock budget.
- Maintainers can discover the scenario from existing golden / agent e2e docs
  (minimal doc touch as needed).
- Unticketed follow-ups (if any) are recorded only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

Acceptance (from Jira): **Golden or agent_e2e coverage waits for a product
dialog to appear after an action.**

## Task Description

**Problem:** Settle helpers are covered with delayed fixture widgets
(`tests/test_ui_wait.py`). The golden flow settles the **response panel** after
Send (`tests/test_agent_golden_e2e.py`). Neither path waits for a **product
dialog** (for example Settings after opening settings, or a confirm dialog) to
appear after an action. PYPOST-837 and PYPOST-838 explicitly deferred that
coverage.

**Business need:** Confidence that agents can stabilize real product dialog
opens the same way they stabilize post-Send response UI — so dialog flows are
not flaky-prone or falsely assumed covered.

### In Scope

- One (or a small set of) golden / `agent_e2e` scenario(s) that:
  1. Drive a product action known to open a dialog (primary candidate:
     open Settings via the settings control; confirm/other product dialogs
     acceptable if they equally prove “dialog appears after action”).
  2. Wait until the product dialog is present using shared settle waits.
  3. Fail with diagnosable context if the dialog never appears within budget.
- Minimal documentation so the coverage is discoverable next to golden /
  agent e2e guidance.
- Reuse of existing agent lifecycle, identity, actions, snapshot, and wait
  capabilities — composition proof, not a new wait subsystem.

### Out of Scope

- Redesigning settle/wait condition helpers (already PYPOST-837 / PYPOST-852).
- Expanding the golden Send → status/body scenario itself beyond what is needed
  to attach or sibling a dialog-settle proof.
- Full Settings dialog functional testing (encryption, bind validation, theme,
  etc. — already covered by dedicated settings tests).
- Full product dialog matrix (every confirm / message box in the app).
- Broader agent-e2e packaging / `make` redesign.
- Network MCP tools for waits.
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: Coverage exists under golden and/or `@pytest.mark.agent_e2e` that
  performs a product UI action which opens a product dialog.
- FR2: After that action, coverage **waits** until the product dialog is
  present (settled) before treating the step as successful.
- FR3: The wait is bounded by a timeout; failure identifies the dialog-settle
  step (not a bare hang or silent pass).
- FR4: The wait uses the shared agent settle/wait surface (same family of
  capabilities used after Send in the golden flow), not an ad-hoc sleep.
- FR5: The scenario runs deterministically under the project’s offscreen GUI /
  agent e2e path.
- FR6: Existing golden Send → response coverage remains valid; this story adds
  dialog settle proof without removing the response settle proof.
- FR7: Docs (or an existing umbrella table) mention the dialog-settle coverage
  so maintainers can find and run it.

## Non-Functional Requirements

- **Boundedness:** Dialog settle must not hang CI indefinitely; wall-clock
  timeouts are mandatory.
- **CI suitability:** Runs under offscreen / standard `make test-agent-e2e`
  (or project-equivalent) selection.
- **Minimalism:** One clear product-dialog settle proof is enough; not a full
  dialog regression suite.
- **Compatibility:** Composes with lifecycle ready, stable identities, actions,
  snapshot, and existing waits.
- **Discoverability:** Maintainers can find how to run the coverage without
  reverse-engineering tests alone.
- **No production → tests imports:** Production agent code must not import from
  `tests/`.

## Constraints and Assumptions

- Programming language: Python.
- Parent / source debt: PYPOST-852 TD-1 (also noted as PYPOST-837 TD-3 and
  PYPOST-838 missing product-dialog settle).
- Product Settings is opened from a stable settings control on the main window;
  Settings is a real product dialog (window title “Settings”).
- Modal product dialogs may block the UI event loop while open; coverage must
  still demonstrate “wait until dialog appears” and complete under a bounded
  budget without leaving the harness stuck.
- “After Send” in the original debt note does not require inventing a new Send
  confirm dialog if Send does not open one; Settings open (or another existing
  product dialog path) satisfies the acceptance bar.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval gate / no Jira updates in this step).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| AI agent / harness | Drives action, waits for dialog, asserts settle |
| Product dialog | Real app dialog (e.g. Settings) that appears after an action |
| Product action | User-facing control interaction that opens the dialog |
| Settle wait | Bounded wait until the dialog is present |
| Golden / agent_e2e coverage | Automated proof path in CI |
| Failure diagnostics | Context when the dialog never appears in time |

Interaction overview:

1. Harness launches PyPost and reaches UI ready.
2. Harness performs a product action that opens a dialog (e.g. open Settings).
3. Harness waits until the product dialog is present (this story’s proof).
4. On timeout, harness fails with diagnosable dialog-settle context.
5. Harness completes cleanup without hanging CI.
6. Existing Send → response golden settle remains a separate proof.

## Q&A

- Q: Why is this a separate debt ticket from PYPOST-837 / PYPOST-838?
  A: Helpers and the Send golden shipped without product-dialog settle;
  deferred explicitly as Medium debt (837 TD-3 → 852 TD-1 → this ticket).

- Q: Must coverage be inside `test_agent_golden_e2e.py` specifically?
  A: Jira accepts **golden or agent_e2e**. Either placement is fine if the
  scenario is marked and runnable with the agent e2e workflow and documented.

- Q: Does “after Send” require a dialog after Send?
  A: No. Acceptance is “waits for a product dialog to appear after an action.”
  Settings open is the primary real product path; inventing a Send confirm is
  out of scope.

- Q: Are synthetic delayed-widget waits enough?
  A: No. Those already exist; this story requires a **product** dialog.

- Q: Must Settings dialog functional behavior be asserted deeply?
  A: No. Presence/settle after open is the acceptance bar; deep settings
  coverage stays in existing settings tests.

- Q: Why not only document the gap?
  A: The business value is automated confidence in CI, not documentation of
  missing coverage.
