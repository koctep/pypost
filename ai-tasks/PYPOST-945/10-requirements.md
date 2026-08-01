# PYPOST-945: Fixture keyClicks for QPlainTextEdit / QTextEdit

## Goals

[PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) delivered opt-in
fill-via-keyClicks on `QLineEdit`, `QPlainTextEdit`, and `QTextEdit`. Fixture
behavioral proof existed only for `QLineEdit`; plain and rich text editors were
accepted by the type guard but not exercised in CI.

This optional debt closes that gap so regressions on the keyClicks fill path for
body-style editors are caught without relying on golden flows.

Source: [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917)
`ai-tasks/PYPOST-917/60-tech-debt.md` TD-2 →
[PYPOST-945](https://pypost.atlassian.net/browse/PYPOST-945).

## Programming Language

Python 3.10+ for pytest Qt fixture proofs. Developer docs in English Markdown.

## User Stories

- As a **maintainer**, I want fixture tests that call
  `ui_fill(..., via_key_clicks=True)` on `QPlainTextEdit` and `QTextEdit`, so
  the opt-in keystroke fill path is proven for body-style editors.
- As a **maintainer**, I want tests to mirror the existing line-edit keyClicks
  fixture pattern (isolated widget, `find_widget`, final text assert).
- As a **CI owner**, I want fast offscreen fixtures with explicit timeouts and
  no product behavior change.

## Definition of Done

- Automated tests cover opt-in keyClicks fill on fixture `QPlainTextEdit` and
  `QTextEdit` (Jira acceptance).
- Existing line-edit, session, and caplog keyClicks tests stay green.
- Steps 1–8 workflow artifacts exist under `ai-tasks/PYPOST-945/`.
- No intentional product runtime change beyond locking behavioral coverage.

## Task Description

**Problem:** `tests/test_ui_actions.py::test_ui_fill_via_key_clicks_on_fixture`
proves keyClicks fill on a fixture `QLineEdit` only. `ui_fill` accepts
`QPlainTextEdit` and `QTextEdit` in production, but no fixture test exercises
the opt-in path on those types.

**Business need:** Optional hardening — behavioral coverage for plain/rich text
editors when golden flows type into body fields via keystroke fill.

### In Scope

- Add isolated plain/rich text fixtures and keyClicks fill tests in
  `tests/test_ui_actions.py`.
- Complete Steps 1–8 workflow artifacts.
- Optional cross-links in `doc/dev/` (Step 8).

### Out of Scope

- Production changes to `ui_fill` or session mirror (already delivered in
  PYPOST-917).
- Caplog scalar asserts for plain/rich editors (line-edit caplog suffices).
- `textChanged` multi-emit asserts (PYPOST-946).
- Per-key delay kwarg (PYPOST-947).
- Live `agent_e2e_session` body-editor keyClicks smoke.

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | Fixture test: `ui_fill(..., via_key_clicks=True)` on `QPlainTextEdit` leaves expected plain text. |
| FR2 | Fixture test: `ui_fill(..., via_key_clicks=True)` on `QTextEdit` leaves expected plain text. |
| FR3 | Tests use `find_widget`, type checks, and `try`/`finally` teardown like existing fill tests. |
| FR4 | Existing line-edit keyClicks, session, and caplog tests remain green. |

## Non-Functional Requirements

- NFR1: Test-only change; no product runtime change expected.
- NFR2: Explicit pytest timeout via existing module `pytestmark` on
  `tests/test_ui_actions.py` (`timeout(60)`).
- NFR3: Offscreen Qt fixture only; no live network.
- NFR4: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Production `ui_fill` keyClicks branch is type-agnostic after the trio guard
  (`pypost/agent/ui_actions.py`, PYPOST-917).
- Line-edit fixture test is the template to mirror
  (`test_ui_fill_via_key_clicks_on_fixture`).
- Autonomous batch run: user approval gates pre-approved for Steps 1–8;
  Jira updates and git commit are out of band for this execution.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Opt-in fill action | Whole-string fill via keystroke simulation |
| Plain text editor | Multi-line body field (`QPlainTextEdit`) |
| Rich text editor | Formatted body field (`QTextEdit`) |
| Fixture proof | Offscreen widget test locking fill behavior |

## Q&A

| Q | A |
| --- | --- |
| Why test if type guard already accepts both? | Line-edit proof does not exercise plain/rich focus/keyClicks paths in CI. |
| Must session body fill be tested too? | No — fixture scope matches line-edit keyClicks proof; session URL smoke stays separate. |
| Product impact? | None — test hygiene only unless test reveals a regression. |
| Source of the debt item? | [PYPOST-917 TD-2](../PYPOST-917/60-tech-debt.md) → [PYPOST-945](https://pypost.atlassian.net/browse/PYPOST-945). |
