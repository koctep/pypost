# PYPOST-870: Optional caplog proof for agent_e2e_http_stub_installed

## Goals

Maintainers need automated proof that the agent e2e HTTP stub emits the
documented install log event `agent_e2e_http_stub_installed`. Today the event
is produced and catalogued, but no test asserts it. Closing this optional
logging-catalog gap makes regressions in the stub-install signal detectable in
CI without relying on manual log inspection.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want an automated check that installing the shared
  HTTP stub emits `agent_e2e_http_stub_installed`, so logging-catalog
  regressions are caught early.
- As a **contributor**, I want that check to follow the same timeout and
  caplog patterns as other agent e2e HTTP / packaging log proofs, so new
  proofs stay consistent with the suite.
- As a **desktop user** (indirect), I want this debt work not to change product
  UX — only to lock in existing HTTP stub observability.

## Definition of Done

- An automated check asserts that `agent_e2e_http_stub_installed` is emitted
  when the shared HTTP stub is installed (acceptance: Test asserts the install
  log event).
- The check uses caplog (or equivalent project-allowed capture) scoped to the
  HTTP fixture logger.
- The check declares an explicit pytest timeout marker (module, class, or
  function scope).
- Steps 1–8 task artifacts exist for PYPOST-870.
- No intentional change to product UX or successful stub behavior beyond
  locking the install-event contract.

## Task Description

**Problem:** PYPOST-859 delivered the shared HTTP stub that logs
`agent_e2e_http_stub_installed name=<catalog_or_custom>`, but Step 7 noted
optional missing coverage: no automated assert of that event. Source:
[PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870), from
[PYPOST-859](https://pypost.atlassian.net/browse/PYPOST-859)
`ai-tasks/PYPOST-859/60-tech-debt.md` — Optional caplog proof for HTTP stub
install event. Sibling packaging pattern:
[PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867).

**Business need:** Close this low-priority testing/observability debt so
HTTP stub install logs remain part of the verified contract.

### In Scope

- Adding a focused automated check for `agent_e2e_http_stub_installed`
  emission on stub install.
- Using isolation so the check does not require a live GUI or network path.
- Completing Steps 1–8 workflow artifacts.
- Updating developer docs that describe HTTP stub logging proofs if needed.

### Out of Scope

- Changing stub install behavior, catalog entries, URL router, or GUI Send
  scenarios.
- Sibling hygiene already owned by other tickets (seed POST GUI, response
  panel helpers, etc.).
- New product features or UI changes.

## Functional Requirements

- FR1: The automated check records that `agent_e2e_http_stub_installed` is
  emitted when `stub_agent_e2e_http` (or equivalent) is entered.
- FR2: The check includes the documented `name=` token for at least one
  catalog/custom install so catalog regressions are meaningful.
- FR3: The check isolates stub-install logging without requiring live network
  or a GUI session.
- FR4: Maintainers can discover the check alongside other agent e2e HTTP
  coverage (same module family or clearly named HTTP-stub-log module).

## Non-Functional Requirements

- NFR1: Explicit pytest timeout marker on the new check (or inherited module
  marker).
- NFR2: Caplog assertion scoped to the HTTP fixture logger
  (`pypost.fixtures.agent_e2e_http` or equivalent).
- NFR3: Prefer fast, deterministic unit style (no offscreen Qt).
- NFR4: No secrets or live host dependency in the proof scenario.

## Constraints and Assumptions

- The HTTP stub and install event already exist from PYPOST-859; this task
  primarily adds verification.
- Autonomous batch run: user approval gates are pre-approved for Steps 1–8;
  Jira updates and git commit are out of band for this execution.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| HTTP stub install | Shared context that patches send_request for agent e2e |
| Stub installed event | Named log signal that the stub was installed |
| Name token | Distinguishes catalog / custom / router installs |
| Caplog proof | Automated assert of the install event |

## Q&A

| Q | A |
| --- | --- |
| Why assert logs if the stub already works? | Catalog/event regressions are invisible without a proof; optional debt from PYPOST-859. |
| Must every catalog name be covered? | Acceptance is the install event; one meaningful `name=` (e.g. `golden_ok`) is enough. |
| Product impact? | None — test/docs hygiene only. |
| Source of the debt item? | [PYPOST-859 tech debt](../PYPOST-859/60-tech-debt.md) → [PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870). |
| Pattern to mirror? | [PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867) packaging-logs caplog proof. |
