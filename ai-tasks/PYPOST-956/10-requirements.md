# PYPOST-956: Shared Send settle + timeout rewrap helper

## Goals

[PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901) introduced a
mapping multi-URL GUI Send scenario that waits for response panel settle via a
local `_wait_response` helper. That helper rewraps `UiWaitTimeoutError` with a
stable step name and a compact response-panel excerpt — the same diagnosability
shape already shared for identity-scoped text waits in env GET and seed POST
flows ([PYPOST-948](https://pypost.atlassian.net/browse/PYPOST-948)).

The mapping module is now the **third** GUI Send consumer carrying the same
try/except + excerpt rewrap shape (golden inline text-wait, env/seed via
`wait_response_after_send`, mapping snapshot-wait local + companion inline
duplicate from [PYPOST-955](https://pypost.atlassian.net/browse/PYPOST-955)).
Maintainers must keep two copies of the rewrap contract in one module and risk
drift between happy-path and forced-timeout companions.

**Business why:** Consolidate Send settle timeout rewrap into one shared test
helper so agent e2e Send scenarios stay DRY, diagnosable, and consistent —
without changing what users see or what CI asserts on success or failure paths.

Source: [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901)
`60-tech-debt.md` TD-2 (Low). Parent debt area:
[PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901). Browse:
[PYPOST-956](https://pypost.atlassian.net/browse/PYPOST-956).

## Programming Language

Python 3.10+ (`.cursor/lsr/do-python.md`). Test-only changes under the
project’s `agent_e2e` harness path. Task artifacts in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **agent e2e maintainer**, I want mapping Send settle to call a shared
  helper under `tests/helpers/` instead of a module-local `_wait_response`, so
  timeout rewrap logic is defined once and reused across Send scenarios.
- As a **maintainer of forced-timeout companions** (PYPOST-955 mapping GET
  companion), I want the companion to reuse the same rewrap helper with a
  configurable settle budget, so happy-path and failure-path diagnostics cannot
  drift apart.
- As an **AI agent / harness author**, I want Send settle timeouts to continue
  carrying stable step identifiers and compact response excerpts, so automation
  failures remain actionable after the refactor.
- As a **CI runner**, I want the full `agent_e2e` suite to stay green under
  `make test-agent-e2e` with no change in acceptance meaning for existing
  scenarios.

## Definition of Done

- A **shared helper** lives under `tests/helpers/` and encapsulates the Send
  settle timeout rewrap contract (step + `response_excerpt` on
  `UiWaitTimeoutError`).
- The mapping multi-URL GUI Send scenario (`PYPOST-901`) uses the shared helper
  for snapshot-based response settle instead of a local `_wait_response`
  definition.
- Existing Send scenarios that already use `wait_response_after_send` (env GET,
  seed POST, and siblings from PYPOST-948) remain behaviorally unchanged unless
  they opt into a shared rewrap primitive without altering diagnostics.
- Forced-timeout companion coverage from PYPOST-955 continues to pass with the
  same asserted step name and excerpt presence/type.
- Full `agent_e2e` suite green under `make test-agent-e2e`.
- No production code or user-facing behavior changes.
- Unticketed follow-ups (if any) recorded only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

Acceptance (from Jira): **Shared helper under tests/helpers used by Send
scenarios; behavior unchanged.**

## Task Description

**Problem:** Snapshot-based mapping Send settle duplicates the timeout rewrap
shape that env GET / seed POST already centralize for text-wait settle. The
mapping module defines local `_wait_response`, and its PYPOST-955 companion
inlines an identical rewrap block — two copies in one file, with the third GUI
Send pattern now present across the harness family.

**Business need:** Extract the shared rewrap + settle wrapper so Send scenarios
import one helper, preserve existing diagnostics contracts, and reduce
copy-paste maintenance — test hygiene only, no product change.

### In Scope

- Shared helper module or extension under `tests/helpers/` for Send settle
  timeout rewrap (snapshot-based path at minimum; optional shared rewrap
  primitive for text-wait path if it reduces duplication without behavior
  change).
- Migrate mapping multi-URL GUI module to import and call the shared helper on
  happy-path GET and POST Send settle waits.
- Refactor PYPOST-955 mapping GET forced-timeout companion to reuse the shared
  helper (same rewrap contract, near-zero timeout budget).
- Convention or inventory lock proving mapping module no longer defines local
  `_wait_response`.
- Verify `make test-agent-e2e` green.

### Out of Scope

- Changing production Send settle, wait APIs, or response panel behavior.
- Migrating golden Send inline text-wait rewrap to the shared helper (optional
  follow-up; golden was explicitly deferred in PYPOST-948).
- Changing env GET / seed POST happy-path settle mechanism (already on
  `wait_response_after_send`).
- New Send scenarios, mapping router rules, or multi-URL regression matrix.
- Caplog proof for `name=url_router` ([PYPOST-957](https://pypost.atlassian.net/browse/PYPOST-957)).
- Optional POST mapping forced-timeout companion
  ([PYPOST-955](https://pypost.atlassian.net/browse/PYPOST-955) follow-up).
- User-facing product docs (`doc/user/`).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: A shared Send settle helper exists under `tests/helpers/` and is importable
  by agent e2e Send consumer modules.
- FR2: The helper rewraps `UiWaitTimeoutError` with stable `step` and
  `response_excerpt` diagnostics matching the existing mapping / env / seed
  contract (no regression in failure message shape or diagnostic keys).
- FR3: The mapping multi-URL happy-path module uses the shared helper for both
  GET and POST Send snapshot settle waits; local `_wait_response` is removed.
- FR4: The PYPOST-955 mapping GET forced-timeout companion uses the shared
  helper (or its rewrap primitive) instead of an inline duplicate block.
- FR5: Env GET, seed POST, double-body, and presentation-matrix Send scenarios
  that already call `wait_response_after_send` remain passing with unchanged
  acceptance meaning.
- FR6: Happy-path mapping multi-URL panel asserts and forced-timeout companion
  assertions (`step`, `response_excerpt`) remain valid.
- FR7: A structural convention test locks the mapping module to the shared
  helper (no local `_wait_response` definition).

## Non-Functional Requirements

- **Behavior preservation:** Refactor only; no intentional change to timeout
  budgets, step names, message prefixes, or diagnostic payloads on existing
  paths.
- **CI suitability:** Runs under offscreen / standard `make test-agent-e2e`
  selection.
- **Minimalism:** Focused helper extraction; not a broad golden migration or
  new scenario matrix.
- **No production impact:** Harness / test hygiene only.
- **No production → tests imports:** Production agent code must not import from
  `tests/`.
- **Typing and style:** Follow `.cursor/lsr/do-python.md`; per-test or module
  timeout markers remain mandatory per `.cursor/lsr/do-testing.md`.
- **English docs;** line length ≤ 100 where practical.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Parent debt: PYPOST-901 TD-2 (Low); inherits step names
  `wait_response_after_mapping_get_send` and
  `wait_response_after_mapping_post_send` from PYPOST-901 observability.
- Existing shared text-wait helper: `wait_response_after_send` in
  `tests/helpers/agent_e2e_send_settle.py` (PYPOST-948).
- Mapping settle uses **snapshot predicate** readiness (`wait_for_snapshot`), not
  identity-scoped text waits — the new or extended helper must support that
  path.
- Forced-timeout companions require a **configurable timeout** (near-zero
  budget); happy path uses `SEND_SETTLE_TIMEOUT_S` (15 s) from
  `tests/helpers/agent_e2e_send.py`.
- Companion may use an impossible snapshot predicate (`lambda _: False`) with
  short timeout — same intent as PYPOST-955 architecture.
- Step 1–2 review treated as pre-approved under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Shared Send settle helper | Single definition of timeout rewrap + settle wait |
| Snapshot-based Send settle | Mapping multi-URL waits on panel snapshot predicate |
| Text-wait Send settle | Env / seed / sibling flows via `wait_response_after_send` |
| Timeout rewrap contract | Stable `step` + `response_excerpt` on forced failure |
| Mapping multi-URL scenario | PYPOST-901 happy-path GET + POST Sends under one stub |
| Mapping timeout companion | PYPOST-955 forced GET settle failure diagnostics lock |
| Convention lock | Structural proof mapping module imports shared helper |
| CI / agent_e2e runner | Verifies suite green after refactor |

Interaction overview:

1. Maintainer adds or extends shared helper under `tests/helpers/`.
2. Mapping happy-path tests call shared helper after each Send click.
3. Mapping timeout companion calls same helper with short timeout budget.
4. On settle success, behavior unchanged — panel asserts proceed as today.
5. On settle timeout, rewrapped `UiWaitTimeoutError` carries same diagnostics.
6. Convention test fails until local `_wait_response` is removed.
7. Full `agent_e2e` suite confirms no regression across Send scenarios.

## Q&A

- Q: Why extract now if PYPOST-901 deferred this as low priority?
  A: The trigger condition is met — a third GUI Send module (mapping) copies the
  same try/except + excerpt shape, and PYPOST-955 added a second inline copy in
  the same module.

- Q: Does this replace `wait_response_after_send`?
  A: No. Text-wait Send scenarios keep using it. This task adds or extends shared
  coverage for the **snapshot-based** mapping path (and shared rewrap primitive
  where it reduces duplication without behavior change).

- Q: Must golden adopt the shared helper?
  A: Out of scope for acceptance. Golden inline rewrap may remain; optional
  follow-up in `60-tech-debt.md`.

- Q: Will step names or message prefixes change?
  A: No intentional change. Mapping keeps
  `wait_response_after_mapping_get_send` / `_post_send` and existing message
  prefix strings.

- Q: Does this change production behavior?
  A: No. Test-only refactor; no new production API or log streams.

- Q: Jira / commit in this run?
  A: No — parent orchestrator owns later phases.
