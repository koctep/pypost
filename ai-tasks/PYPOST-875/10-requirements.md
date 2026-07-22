# PYPOST-875: Auto-dump for direct AgentAppSession constructions

## Goals

When an agent e2e scenario fails, authors and CI need the same masked UI
snapshot + diagnostics dump whether the test used a shared packaging fixture
or constructed an agent session directly (for example multi-session isolation).

Today only fixture-backed tests auto-dump on assert fail. Direct constructions
skip the failure hook, so triage is inconsistent and authors must remember a
manual helper call.

This debt comes from [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860)
tech-debt: auto-dump was limited to shared fixtures; direct constructions were
left as follow-up.

## Programming Language

Python (pytest agent e2e harness). Guides: `.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`. Developer documentation in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **test author**, I want failure dumps when my test builds an agent
  session directly (not only via packaging fixtures), so multi-session and
  lifecycle isolation failures are diagnosable the same way as golden/env-pack
  failures.
- As a **CI maintainer**, I want direct-construction failures to leave the same
  on-disk artifact layout under `artifacts/agent_e2e/`, so uploads and local
  triage stay uniform.
- As a **future maintainer**, I want docs and automated checks that state when
  auto-dump applies to direct constructions, so the contract does not silently
  drift.

## Definition of Done

- On call-phase failure, tests that construct an agent session directly (and
  opt into the same dump path as fixtures) produce masked UI snapshot +
  diagnostics under the documented artifact root.
- Existing fixture-backed auto-dump behavior remains intact.
- Secrets policy from PYPOST-860 remains: dumps stay masked; no cleartext
  secret packaging.
- Docs describe how direct constructions participate in auto-dump.
- Automated checks lock the new behavior (red then green in Steps 3–4).
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

## Task Description

**Problem:** PYPOST-860 auto-dumps on assert fail only when the test requested
`agent_e2e_session` or `seeded_agent_e2e_session`. Tests that construct
`AgentAppSession` themselves (multi-session isolation, some lifecycle smokes)
skip the hook unless authors call the dump helper manually.

**Business need:** Consistent failure triage for all in-process agent e2e
sessions — fixture or direct — without expanding product UI scope.

### In Scope

- Research packaging fixtures vs direct construction and the failure dump path.
- Extend auto-dump so direct constructions can participate (opt-in or
  equivalent equivalent coverage for known isolation patterns).
- Keep fixture auto-dump unchanged for golden / env-pack paths.
- Align `doc/dev` failure-artifact guidance with the new contract.
- Lock behavior with automated tests.

### Out of Scope

- Changing snapshot masking or dump file layout from PYPOST-860.
- CI upload wiring (PYPOST-874).
- Narrowing dump-helper exception types (PYPOST-876).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions (orchestrator owns those).

## Functional Requirements

- FR1: Call-phase failures involving a live direct-construction agent session
  that participates in the dump path write the same artifact pair as fixtures
  (`ui_snapshot.json` + `diagnostics.json`).
- FR2: Fixture-backed auto-dump continues to work without requiring per-test
  manual dump calls.
- FR3: Diagnostics identify that the dump came from a direct construction
  (or equivalent clear provenance) when fixtures were not used.
- FR4: Dump remains best-effort: dump errors must not replace the original test
  failure.
- FR5: Docs state how authors enable or rely on auto-dump for direct
  constructions.
- FR6: Automated checks prove direct-construction failure produces artifacts.

## Non-Functional Requirements

- NFR1: Reuse existing dump helper and masking; do not duplicate snapshot logic.
- NFR2: Success paths stay unchanged (no dump on pass).
- NFR3: Docs stay in English; line length ≤ 100 where practical.
- NFR4: Per-test timeouts remain mandatory on new/changed tests.

## Constraints and Assumptions

- Parent debt: PYPOST-860 `60-tech-debt.md` — “Auto-dump for direct
  `AgentAppSession` constructions” → this ticket.
- Known direct users today include multi-session isolation and some lifecycle
  smokes under `tests/`.
- Default artifact root and env override (`PYPOST_AGENT_E2E_ARTIFACTS`) stay as
  in PYPOST-860.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Shared session fixture | Packaging path that already auto-dumps |
| Direct agent session | Test-owned session without those fixtures |
| Failure artifact dump | Masked UI snapshot + diagnostics on disk |
| Failure hook | Call-phase trigger that selects a live session |
| Contributor triage | Read dumps after red local/CI agent e2e |

## Q&A

| Q | A |
| --- | --- |
| Why not only document manual helper use? | Parent already noted manual call; ticket asks for auto-dump parity. |
| Why keep fixture path? | Golden/env-pack DoD from 860 must not regress. |
| Jira / commit in this run? | No — user directed; worklog block only for parent. |
