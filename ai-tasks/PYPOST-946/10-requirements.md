# PYPOST-946: Optional textChanged multi-emit assert

## Goals

[PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) delivered opt-in
fill-via-keyClicks and fixture tests that assert **final text** only. That
proves the field ends up correct but not that keystrokes were delivered
incrementally (vs a one-shot setter path).

This optional debt adds a signal-count assertion so regressions that bypass
per-key delivery are caught in CI.

Source: [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917)
`ai-tasks/PYPOST-917/60-tech-debt.md` TD-3 →
[PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946).

## Programming Language

Python 3.10+ for pytest Qt fixture proofs. Developer docs in English Markdown.

## User Stories

- As a **maintainer**, I want a fixture test that counts `textChanged`
  emissions during `ui_fill(..., via_key_clicks=True)`, so keystroke realism
  is proven beyond final-text equality.
- As a **maintainer**, I want the expected emission count documented in the
  test (Qt offscreen behaviour), so future Qt upgrades can adjust asserts
  deliberately.
- As a **CI owner**, I want a test-only change with explicit timeouts and no
  product behaviour change.

## Definition of Done

- Automated test asserts `textChanged` fires per keystroke on the line-edit
  keyClicks fixture path (or documents the expected count) — Jira acceptance.
- Existing keyClicks fill tests stay green.
- Steps 1–8 workflow artifacts exist under `ai-tasks/PYPOST-946/`.
- No intentional product runtime change.

## Task Description

**Problem:** `test_ui_fill_via_key_clicks_on_fixture` only checks
`line.text() == fill_text`. A broken implementation that used setters after
clear would still pass.

**Business need:** Optional hardening — lock per-key signal delivery on the
opt-in keyClicks fill path.

### In Scope

- Add one fixture test with `textChanged` emission counting in
  `tests/test_ui_actions.py`.
- Document expected count for empty-start `QLineEdit` offscreen (Qt 6).
- Complete Steps 1–8 workflow artifacts.
- Optional cross-links in `doc/dev/` (Step 8).

### Out of Scope

- Production changes to `ui_fill` or session mirror.
- Plain/rich `textChanged` asserts (different signal arity / clear semantics).
- Per-key delay kwarg (PYPOST-947).
- Session body-editor keyClicks smoke (PYPOST-976).

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Fixture test connects to `textChanged` before opt-in keyClicks fill. |
| FR2 | Test asserts emission count matches documented per-keystroke expectation. |
| FR3 | Test asserts final text still matches fill string. |
| FR4 | Existing keyClicks fill tests remain green. |

## Non-Functional Requirements

- NFR1: Test-only change; no product runtime change expected.
- NFR2: Explicit pytest timeout via module `pytestmark` on
  `tests/test_ui_actions.py` (`timeout(60)`).
- NFR3: Offscreen Qt fixture only; no live network.
- NFR4: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Production `ui_fill` keyClicks branch unchanged (`pypost/agent/ui_actions.py`,
  PYPOST-917).
- Empty-start `QLineEdit`: `clear()` is silent; `QTest.keyClicks` emits once
  per character (verified offscreen during architecture).
- Autonomous batch run: user approval gates pre-approved for Steps 1–8; Jira
  updates and git commit are out of band.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Opt-in fill action | Whole-string fill via keystroke simulation |
| Signal emission proof | Count of `textChanged` during fill |
| Fixture proof | Offscreen widget test locking fill behaviour |

## Q&A

| Q | A |
| --- | --- |
| Why line edit only? | Primary keyClicks fixture; plain/rich use no-arg `textChanged` and clear emits once even when empty — separate counts if needed later. |
| What if Qt changes emit count? | Test documents expected count; update assert with deliberate comment when Qt behaviour shifts. |
| Product impact? | None — test hygiene only unless test reveals regression. |
| Source of the debt item? | [PYPOST-917 TD-3](../PYPOST-917/60-tech-debt.md) → [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946). |
