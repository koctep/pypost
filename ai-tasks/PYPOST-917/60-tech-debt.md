# PYPOST-917: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: opt-in `via_key_clicks` on `ui_fill` (module + session);
default remains clear+setter; fixture and session tests prove the keyClicks
path; DEBUG scalar `via_key_clicks` present. Developer docs for default vs
keystroke vs `ui_send_key` delivered in Step 8 (`doc/dev/ui_actions.md`).

## Shortcuts Taken

- **Extend `ui_fill` instead of a sibling** — One agent fill primitive;
  keyword-only `via_key_clicks=False` keeps every existing call site on
  setters (matches architecture / parent debt wording).
- **Qt default keyClicks delay (`-1`)** — No per-key sleep API; keeps
  opt-in path suitable for offscreen CI (NFR5). Callers who need paced
  typing can still loop `ui_send_key` (out of scope here).
- **Same widget trio as setters** — `QLineEdit` / `QPlainTextEdit` /
  `QTextEdit` only; no new control types.
- **Clear → focus → `QTest.keyClicks`** — Mirrors `ui_send_key` focus
  pattern; does not attempt native OS / IME plugin simulation (Qt Test
  internal events only — documented Qt limitation, accepted).
- **Docs in Step 8** — `doc/dev/ui_actions.md` documents default vs
  keystroke fill and vs `ui_send_key` (completed).

## Code Quality Issues

- KeyClicks branch shares the post-action `_pump` and DEBUG log with the
  setter path — good; no duplication to clean.
- Setter path still splits `QLineEdit` (`setText`) vs plain/rich
  (`setPlainText`); keyClicks path is type-agnostic after the trio guard.
  Fine; no shared helper warranted yet.
- Optional architecture note (assert `textChanged` count > 1 for realism)
  was not added to green tests — final-text assertions suffice for
  acceptance (TD-3).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Default fill (setter) on fixture | Covered (`test_ui_fill_on_fixture`) |
| Opt-in keyClicks on fixture `QLineEdit` | Covered |
| Session `ui_fill(..., via_key_clicks=True)` | Covered |
| Caplog `via_key_clicks=false` + no fill text | Covered |
| Caplog `via_key_clicks=true` scalar | Not dedicated — same log call; false-path covers shape (TD-1) |
| KeyClicks on `QPlainTextEdit` / `QTextEdit` | Not covered — trio accepted by type guard; fixture is line-edit only (TD-2) |
| Explicit timeout markers | **Present** — module `timeout(60)` |

## Performance Concerns

None for the default path. Opt-in `QTest.keyClicks` is slower than
`setText` by design; callers must opt in. No mandatory delay keeps CI
cost bounded.

## Deviations from Architecture

None material. Delivered `via_key_clicks` keyword on module + session,
clear+focus+keyClicks branch, DEBUG scalar, and dual-mode tests as
planned. Docs update left for Step 8 as sequenced in
`20-architecture.md`.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| This story | PYPOST-917 (closing after Step 8 docs) |
| Source debt | PYPOST-851 TD-2 / PYPOST-836 optional fill-via-keyClicks |

### NON-BLOCKER

| ID | Priority | Item | Notes | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Low | Caplog assert for `via_key_clicks=true` | Mirror false-path scalar check; optional hardening only. | [PYPOST-944](https://pypost.atlassian.net/browse/PYPOST-944) |
| TD-2 | Low | Fixture keyClicks coverage for plain/rich text edits | Line-edit proof + type guard cover acceptance; add if a golden flow types into body editors via this mode. | [PYPOST-945](https://pypost.atlassian.net/browse/PYPOST-945) |
| TD-3 | Lowest | Optional `textChanged` multi-emit assert for keyClicks | Proves per-key delivery vs one-shot set; not required for DoD. | [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) |
| TD-4 | Lowest | Optional `delay` kwarg on keyClicks fill | Architecture deliberately omitted; expose only if a harness needs paced typing without `ui_send_key` loops. | [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) |

### Accepted / out of scope (do not ticket)

- Making keyClicks the default for golden / seed flows.
- Replacing `ui_send_key` for single keys / hotkeys.
- Native OS / IME plugin simulation beyond Qt Test events.
- Out-of-process MCP packaging of UI actions (prior PYPOST-836 / 918).
- Step 8 `doc/dev/ui_actions.md` update — completed in this task.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to acceptance |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** (code, tests, FR6 docs) |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — opt-in fill-via-keyClicks is implemented, logged,
documented, and locked by fixture + session tests; remaining items are
optional hardening.
