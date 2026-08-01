# PYPOST-955: Timeout companion for mapping settle diagnostics

## Goals

[PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) delivered happy-path
`agent_e2e` coverage that Sends GET then POST under one Mapping stub, waits for
each response panel to settle, and rewraps timeout failures with stable step
names and a compact response excerpt. That failure-path diagnosability is
**implemented** in the mapping multi-URL settle helper but **not asserted** by
automated coverage — the optional timeout companion was deferred as TD-1 when
PYPOST-901 closed on happy-path acceptance.

Without a dedicated timeout companion, regressions in mapping Send settle failure
diagnostics (missing step, missing response excerpt) can slip through CI while
the happy path stays green. Maintainers and agents then lose actionable context
when mapping multi-URL Send settle fails in automation — the same gap the
golden Send flow already closes with its forced-settle timeout companion
([PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950)).

**Business why:** Lock in diagnosability for mapping multi-URL Send response
settle under `agent_e2e`, matching the confidence level already established for
golden Send response settle timeouts.

Source: [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901)
`60-tech-debt.md` TD-1 (Medium). Parent story:
[PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901). Browse:
[PYPOST-955](https://pypost.atlassian.net/browse/PYPOST-955).

## Programming Language

Python 3.10+ (`.cursor/lsr/do-python.md`). Automated coverage under the
project’s `agent_e2e` harness path. Task artifacts in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **maintainer**, I want an `agent_e2e` companion that forces mapping Send
  settle timeout and asserts failure diagnostics, so regressions in step naming
  or response excerpt are caught in CI — not only when someone manually triggers
  a failure.
- As an **AI agent / harness author**, I want mapping Send settle timeouts to
  carry a stable step identifier and a compact response-panel excerpt, so
  automation logs and CI failures clearly identify which mapping Send (GET or
  POST) failed and what the panel showed at timeout.
- As a **CI / headless runner**, I want the companion to finish under a bounded
  wall-clock budget and not hang the job when the forced timeout path runs.
- As a **sibling story owner** (PYPOST-901 mapping multi-URL GUI), I want this
  companion to extend the existing mapping proof without replacing or weakening
  the happy-path scenario or the golden Send timeout companion pattern.

## Definition of Done

- An `agent_e2e`-marked **timeout companion** exists alongside the PYPOST-901
  mapping multi-URL GUI coverage (same module family as the happy-path proof).
- The companion **forces** mapping Send response settle failure within a
  near-zero budget (same intent as the golden Send timeout companion precedent).
- On forced timeout, assertions verify:
  - The stable mapping settle step identifier matches the Send path under test
    (GET and/or POST per the parent observability contract).
  - A compact response-panel excerpt is present and reflects the panel at
    timeout.
- The full `agent_e2e` suite stays green under `make test-agent-e2e`.
- The existing happy-path mapping multi-URL test remains valid and passing.
- Unticketed follow-ups (if any) are recorded only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

Acceptance (from Jira): **Companion test(s) prove timeout diagnostics for
mapping settle path.**

## Task Description

**Problem:** PYPOST-901 ships mapping Send settle timeout rewrap with step names
`wait_response_after_mapping_get_send` and
`wait_response_after_mapping_post_send` plus `response_excerpt`, but only the
happy path is regression-tested. Failure diagnostics can regress silently.

**Business need:** Automated proof that mapping multi-URL Send settle timeouts
remain diagnosable — parity with the golden Send forced-timeout companion —
without introducing CI hangs or destabilizing the existing happy-path proof.

### In Scope

- One or more `agent_e2e` timeout companions for the mapping multi-URL GUI
  scenario delivered in PYPOST-901.
- Forced near-zero settle budget on the mapping Send response wait so timeout
  occurs deterministically after a GET and/or POST Send under the Mapping stub.
- Assertions on timeout failure diagnostics: step name and response excerpt.
- Bounded execution suitable for standard `make test-agent-e2e` selection.

### Out of Scope

- Changing production Send settle or wait APIs (test-only debt).
- Replacing or duplicating the PYPOST-901 happy-path mapping multi-URL proof.
- Full multi-URL / multi-method regression matrix.
- Mapping router implementation or match rules
  ([PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868)).
- method+URL compound map keys ([PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902)).
- Shared Send settle + timeout rewrap helper extraction
  ([PYPOST-956](https://pypost.atlassian.net/browse/PYPOST-956)).
- Caplog proof for `name=url_router` ([PYPOST-957](https://pypost.atlassian.net/browse/PYPOST-957)).
- Golden Send → response flow changes (separate timeout companion already
  exists).
- User-facing product docs (`doc/user/`).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: Timeout companion coverage exists under `@pytest.mark.agent_e2e` for the
  mapping multi-URL GUI scenario (sibling to the PYPOST-901 happy-path test).
- FR2: The companion forces mapping Send response settle timeout within a
  near-zero budget so failure is deterministic (not dependent on ambient
  timing flakiness).
- FR3: On forced timeout, failure diagnostics include the stable mapping settle
  step identifier from the parent observability contract for the Send path under
  test (GET and/or POST).
- FR4: On forced timeout, failure diagnostics include a compact response-panel
  excerpt (`response_excerpt`) from the parent observability contract.
- FR5: The companion completes without hanging CI under the module’s wall-clock
  timeout budget.
- FR6: Existing happy-path mapping multi-URL test and golden Send timeout
  companion coverage remain passing and unchanged in acceptance meaning.
- FR7: Failure-path diagnosability for mapping Send settle matches the intent
  of the golden Send timeout companion (step + context excerpt on forced
  timeout).

## Non-Functional Requirements

- **Boundedness:** Forced timeout path must not hang CI; module-level timeout
  markers remain mandatory per project testing rules.
- **CI suitability:** Runs under offscreen / standard `make test-agent-e2e`
  selection alongside existing mapping multi-URL coverage.
- **Minimalism:** Focused timeout companion(s); not a full mapping failure
  matrix.
- **No production impact:** Harness / test hygiene only; no product UX or
  live-network behavior change.
- **No production → tests imports:** Production agent code must not import from
  `tests/`.
- **English docs;** line length ≤ 100 where practical.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Parent / source debt: PYPOST-901 TD-1 (Medium); inherits mapping settle step
  names and `response_excerpt` contract from PYPOST-901 observability.
- Reference pattern: golden Send timeout companion precedent — business parity
  for failure-path diagnosability, not a mandate to copy implementation structure
  verbatim.
- Parent observability contract (PYPOST-901): mapping settle step names
  `wait_response_after_mapping_get_send` and
  `wait_response_after_mapping_post_send`, plus `response_excerpt` on timeout
  rewrap.
- Happy-path module uses seed GET / seed POST catalog URLs under one Mapping
  stub; companion may reuse the same stub and UI fill pattern.
- Jira acceptance allows GET **or** POST path coverage; both step names exist in
  the parent contract — companion(s) must lock at least one mapping settle step
  plus excerpt; covering both GET and POST paths is acceptable but not mandated
  unless needed to satisfy the parent diagnostic contract fully.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval gate / no Jira updates in this step).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Timeout companion | Automated proof that forced mapping Send settle failure is diagnosable |
| Mapping settle step | Stable failure identifier for GET or POST Send under Mapping stub |
| Response excerpt | Compact panel snapshot at timeout for triage |
| Forced timeout | Near-zero settle budget to trigger failure deterministically |
| Happy-path mapping multi-URL | PYPOST-901 proof that two Sends under one stub succeed |
| Golden Send timeout companion | Precedent for step + excerpt assertions on forced timeout |
| Mapping stub | Routes each Send’s URL to a canned HTTP outcome |
| CI / agent_e2e runner | Runs suite under bounded budget; must not hang |

Interaction overview:

1. Harness reaches UI ready (same session family as happy-path mapping proof).
2. Companion installs Mapping stub and drives GET and/or POST Send.
3. Companion forces response settle timeout (near-zero budget) on the mapping
   Send wait path.
4. Settle timeout surfaces as a timeout failure with rewrapped diagnostics.
5. Companion asserts step name and response excerpt match the PYPOST-901
   contract for that Send path.
6. Harness completes cleanup without hanging CI.
7. Happy-path mapping multi-URL and golden Send proofs remain separate green
   checks.

## Q&A

- Q: Why is this separate from PYPOST-901 if the rewrap already exists?
  A: PYPOST-901 acceptance was happy-path mapping multi-URL Send; timeout
  diagnostics were implemented but deferred from automated assertion (TD-1).
  This ticket closes that coverage gap.

- Q: Must both GET and POST mapping settle steps be covered?
  A: Jira acceptance requires companion test(s) to prove mapping settle path
  diagnostics. At minimum one forced timeout asserting step + excerpt satisfies
  acceptance; covering both GET and POST step names is desirable when they are
  distinct contracts.

- Q: Which diagnostic fields must be asserted?
  A: At minimum `step` (mapping settle step identifier) and `response_excerpt`
  (string panel excerpt) — the scalars the parent observability contract
  documents on the timeout rewrap path.

- Q: Does this change production behavior?
  A: No. This is test-only debt asserting existing failure diagnostics; no new
  production API or log streams are required for acceptance.

- Q: What if forcing timeout is flaky?
  A: Near-zero budget (same intent as golden Send companion) should make timeout
  deterministic; module wall-clock timeout guards against hangs.

- Q: Jira / commit in this run?
  A: No — parent orchestrator owns later phases.
