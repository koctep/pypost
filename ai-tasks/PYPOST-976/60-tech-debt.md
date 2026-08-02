# PYPOST-976: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: session smoke
`test_ui_fill_via_key_clicks_session_request_body` proves opt-in
`session.ui_fill(REQUEST_BODY_EDIT, …, via_key_clicks=True)` on the live
`CodeEditor` under `agent_e2e_session`; plain-text assert green (~8ms); no
production changes. Closes
[PYPOST-945/60-tech-debt.md](../PYPOST-945/60-tech-debt.md) UT-1.

## Shortcuts Taken

- **Green-on-first-run behavioral proof** — PYPOST-917 already implements
  keyClicks fill for `QPlainTextEdit` / `CodeEditor`; gap was session coverage
  only (Step 3 N/A).
- **POST method select for Body tab visibility** — Minimal arrange vs importing
  `_ensure_body_tab_visible`; matches other agent e2e body fills.
- **Final-text assert only** — No `textChanged` multi-emit check
  ([PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) out of scope).
- **No session caplog for body keyClicks** — Line-edit parametrized caplog
  (PYPOST-944) locks DEBUG scalar shape; body-editor caplog deferred to
  [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977).

## Code Quality Issues

None material. New test mirrors sibling
`test_ui_fill_via_key_clicks_session` (session fixture, `is_ui_ready` guard,
`find_widget` + type assert). Import block expanded for `REQUEST_BODY_EDIT`.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Opt-in keyClicks on fixture `QPlainTextEdit` | Covered (PYPOST-945) |
| Opt-in keyClicks on fixture `QTextEdit` | Covered (PYPOST-945) |
| Session URL `QLineEdit` keyClicks | Covered (PYPOST-917) |
| Session request body `CodeEditor` keyClicks | **Covered (this story)** |
| Caplog `via_key_clicks=true` on body editor | Out of scope — [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977) |
| Caplog on plain/rich fixtures | Out of scope — [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977) |
| `textChanged` multi-emit on body keyClicks | Not covered — [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) |
| Per-key delay kwarg on body | Covered indirectly (PYPOST-947); no body-specific delay smoke |
| Explicit timeout markers | **Present** — module `pytest.mark.timeout(60)` |

## Performance Concerns

None. One additional agent e2e fill adds negligible CI cost (~8ms).

## Deviations from Architecture

None. Test-only change delivered as planned in `20-architecture.md`; production
module graph unchanged.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent UT-1 (session body keyClicks smoke) | This story (PYPOST-976) |
| Caplog keyClicks on plain/rich fixtures + body | [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977) |
| `textChanged` multi-emit asserts | [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) |
| Per-key delay kwarg | [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) (closed) |
| Fill logging contract (production) | [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) |

### NON-BLOCKER

| ID | Priority | Summary | Acceptance |
| --- | --- | --- | --- |
| — | — | ~~Dev doc cross-link for new session smoke~~ | **Addressed (Step 8)** — `test_ui_fill_via_key_clicks_session_request_body` and sibling URL session smoke documented in `doc/dev/ui_actions.md` and `doc/dev/testing.md`. |

### Accepted / out of scope (do not ticket)

- Live HTTP send or golden-flow body typing via keyClicks — fill + assert only.
- Assert full log message string on session body fill — scalar caplog on line edit
  + PYPOST-977 scope.
- Native OS / IME simulation beyond Qt Test events.
- PUT vs POST method select for Body tab — POST chosen for minimal arrange.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** — FR1–FR5 satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — session body-editor keyClicks smoke locks opt-in fill on
the live request body editor; remaining items are optional sibling hardening
(PYPOST-946–977).
