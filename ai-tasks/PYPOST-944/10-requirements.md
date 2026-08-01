# PYPOST-944: Caplog assert for via_key_clicks=true on ui_fill

## Goals

[PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) delivered opt-in
fill-via-keyClicks and DEBUG `ui_action_applied` logging with a
`via_key_clicks` scalar for both default and opt-in modes. The default-mode
caplog proof already asserts `via_key_clicks=false`, but the opt-in true path
has no dedicated caplog assertion — only behavioral tests prove keyClicks fill
works.

This optional debt closes that symmetry gap so a logging regression on the
opt-in fill mode is caught in CI without manual log inspection.

Source: [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917)
`ai-tasks/PYPOST-917/60-tech-debt.md` TD-1 →
[PYPOST-944](https://pypost.atlassian.net/browse/PYPOST-944).

## Programming Language

Python 3.10+ for pytest caplog proofs. Developer docs in English Markdown.

## User Stories

- As a **maintainer**, I want an automated caplog proof that opt-in
  `ui_fill(..., via_key_clicks=True)` emits `via_key_clicks=true` in the
  DEBUG `ui_action_applied` line, so the logging contract stays symmetric with
  the default fill path.
- As a **maintainer**, I want the proof to mirror the existing false-path
  caplog test (same logger, scalar shape, no fill text in logs).
- As a **CI owner**, I want this to remain a fast fixture-style test with no
  live network or product behavior change.

## Definition of Done

- An automated test asserts `via_key_clicks=true` appears in DEBUG caplog when
  opt-in fill is used (Jira acceptance).
- Fill text remains absent from captured logs (existing NFR3 contract).
- Existing default-path caplog and behavioral keyClicks tests stay green.
- Steps 1–8 workflow artifacts exist under `ai-tasks/PYPOST-944/`.
- No intentional product runtime change beyond locking the logging contract.

## Task Description

**Problem:** `tests/test_ui_actions.py::test_ui_action_applied_caplog` asserts
`via_key_clicks=false` for default fill. Opt-in keyClicks fill is covered by
behavioral tests (`test_ui_fill_via_key_clicks_on_fixture`,
`test_ui_fill_via_key_clicks_session`) but not by a caplog scalar assert for
`via_key_clicks=true`.

**Business need:** Optional hardening — symmetric caplog coverage for both fill
modes so DEBUG logging regressions on the opt-in path are visible in CI.

### In Scope

- Add or extend caplog assertion for `via_key_clicks=true` on opt-in
  `ui_fill` in `tests/test_ui_actions.py`.
- Preserve secret/fill-text-not-logged contract from PYPOST-851.
- Complete Steps 1–8 workflow artifacts.

### Out of Scope

- Production changes to `ui_fill`, session mirror, or log message shape
  (already delivered in PYPOST-917).
- KeyClicks coverage for plain/rich text editors (PYPOST-945).
- `textChanged` multi-emit asserts (PYPOST-946).
- Per-key delay kwarg (PYPOST-947).
- Live GUI session caplog for fill (fixture proof sufficient).

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Caplog assert that DEBUG `ui_action_applied` for opt-in fill includes `via_key_clicks=true`. |
| FR2 | Assert uses logger `pypost.agent.ui_actions` at DEBUG (same as false-path test). |
| FR3 | Assert retains scalar shape checks: `primitive=fill`, `widget_id=`, `outcome=ok`, `duration_ms=`. |
| FR4 | Fill text must not appear in caplog output (NFR3 / existing contract). |
| FR5 | Existing `via_key_clicks=false` caplog proof remains covered (same or sibling test). |

## Non-Functional Requirements

- NFR1: Test-only change; no product runtime change expected.
- NFR2: Explicit pytest timeout via existing module `pytestmark` on
  `tests/test_ui_actions.py` (`timeout(60)`).
- NFR3: No fill text or secrets in log assertions beyond existing scalars.
- NFR4: Offscreen Qt fixture only; no live network.
- NFR5: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Production already logs `via_key_clicks=%s` (lowercase) on successful fill
  (`pypost/agent/ui_actions.py`, PYPOST-917).
- Default-path caplog pattern is the template to mirror
  (`test_ui_action_applied_caplog`).
- Autonomous batch run: user approval gates pre-approved for Steps 1–8;
  Jira updates and git commit are out of band for this execution.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Opt-in fill action | Whole-string fill via keystroke simulation |
| ui_action_applied event | DEBUG log after successful UI primitive |
| via_key_clicks scalar | Mode token distinguishing default vs opt-in fill |
| Caplog proof | Automated assert of the logging contract |
| Fixture text input | Offscreen QLineEdit used for fast fill tests |

## Q&A

| Q | A |
| --- | --- |
| Why assert logs if keyClicks fill already works? | Behavioral tests do not lock the DEBUG scalar; false path already has caplog proof. |
| Must session fill be caplog-tested too? | No — fixture-level proof matches false-path scope; session smoke stays behavioral. |
| Product impact? | None — test hygiene only unless test reveals a logging regression. |
| Source of the debt item? | [PYPOST-917 TD-1](../PYPOST-917/60-tech-debt.md) → [PYPOST-944](https://pypost.atlassian.net/browse/PYPOST-944). |
