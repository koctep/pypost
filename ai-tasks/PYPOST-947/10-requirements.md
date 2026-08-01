# PYPOST-947: Optional delay kwarg on keyClicks fill

## Goals

[PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) delivered opt-in
fill-via-keyClicks with Qt default per-key delay (`-1`). Harnesses that need
paced typing without looping `ui_send_key` should be able to opt into a
positive delay on the keyClicks fill path only.

Source: [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917)
`ai-tasks/PYPOST-917/60-tech-debt.md` TD-4 →
[PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947).

## Programming Language

Python 3.10+ for agent UI actions and pytest Qt proofs. Developer docs in
English Markdown.

## User Stories

- As a **harness author**, I want an optional `delay` on opt-in keyClicks fill,
  so I can pace keystrokes for debounced or animation-sensitive UI without
  manual `ui_send_key` loops.
- As a **maintainer**, I want the default fill path unchanged when `delay` is
  omitted, so golden / seed / CI flows stay fast.
- As a **CI owner**, I want a smoke test that proves the delay is forwarded to
  `QTest.keyClicks`, plus developer docs for the keyword.

## Definition of Done

- `ui_fill(..., via_key_clicks=True, delay=<ms>)` forwards `delay` to
  `QTest.keyClicks`; default `-1` when omitted (Qt default).
- Default setter fill and keyClicks fill without `delay` behave as before.
- Session `ui_fill` mirrors the keyword.
- Smoke test + Step 8 dev docs.
- Steps 1–8 workflow artifacts under `ai-tasks/PYPOST-947/`.

## Task Description

**Problem:** Opt-in keyClicks fill always uses Qt default delay. Some harnesses
need explicit per-key pacing on the whole-string fill primitive.

**Business need:** Optional debt — expose paced typing on the existing fill API
without a new primitive or breaking defaults.

### In Scope

- Keyword-only `delay: int = -1` on module and session `ui_fill`.
- Forward `delay` only on the keyClicks branch.
- Fixture smoke test (mock/spy on `QTest.keyClicks`).
- Developer documentation in `doc/dev/`.
- Complete Steps 1–8 workflow artifacts.

### Out of Scope

- Changing default fill mode to keyClicks.
- Logging fill text or mandatory delay in DEBUG lines.
- Replacing `ui_send_key` for single keys / hotkeys.
- Native OS / IME simulation beyond Qt Test.

## Functional Requirements

| ID | Requirement |
| --- | --- |
| FR1 | `ui_fill` accepts optional keyword `delay` (default `-1`). |
| FR2 | When `via_key_clicks=True`, `delay` is passed to `QTest.keyClicks`. |
| FR3 | When `via_key_clicks=False`, default setter path unchanged (`delay` ignored). |
| FR4 | `AgentAppSession.ui_fill` passes through `delay`. |
| FR5 | Existing keyClicks and default fill tests remain green. |

## Non-Functional Requirements

- NFR1: Keyword-only; no positional API breakage.
- NFR2: Explicit pytest timeout via module `pytestmark` on
  `tests/test_ui_actions.py` (`timeout(60)`).
- NFR3: Offscreen Qt fixture for smoke; no live network required.
- NFR4: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Qt signature: `QTest.keyClicks(widget, text, delay=<ms>)` with default `-1`.
- Positive delays slow tests; callers must opt in explicitly.
- Autonomous batch run: no Jira updates or git commit in this session.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Opt-in fill action | Whole-string fill via keystroke simulation |
| Per-key delay | Optional pacing between simulated key clicks |
| Session mirror | Agent convenience API matching module primitive |

## Q&A

| Q | A |
| --- | --- |
| Why not always expose delay in logs? | Fill text and timing details stay out of logs (PYPOST-917 contract); delay is caller-controlled test/harness tuning. |
| Error if `delay` set without `via_key_clicks`? | No — ignored on setter path; simpler API. |
| Replace `ui_send_key` loops? | Optional convenience only; single-key API unchanged. |
| Source of debt? | [PYPOST-917 TD-4](../PYPOST-917/60-tech-debt.md). |
