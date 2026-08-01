# PYPOST-945: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: fixture tests
`test_ui_fill_via_key_clicks_on_plain_text_fixture` and
`test_ui_fill_via_key_clicks_on_rich_text_fixture` prove opt-in
`ui_fill(..., via_key_clicks=True)` on `QPlainTextEdit` and `QTextEdit`;
module green; closes
[PYPOST-917/60-tech-debt.md](../PYPOST-917/60-tech-debt.md) TD-2. No
production code changed.

## Shortcuts Taken

- **Green-on-first-run behavioral proof** — PYPOST-917 already implements
  keyClicks fill for the widget trio; Step 3 N/A (coverage debt only).
- **Isolated fixtures vs extending `_make_fixture`** — Keeps combo/list/tree
  tests lean; mirrors `_make_list_view_fixture` pattern.
- **Final-text assert only** — No `textChanged` multi-emit check (TD-3 /
  PYPOST-946 out of scope).
- **No plain/rich caplog tests** — Line-edit parametrized caplog (PYPOST-944)
  locks DEBUG scalar shape for both fill modes.

## Code Quality Issues

None material. New fixtures reuse `set_widget_id`, `find_widget`, and
`try`/`finally` teardown from existing fill tests.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Opt-in keyClicks on fixture `QLineEdit` | Covered (pre-existing) |
| Opt-in keyClicks on fixture `QPlainTextEdit` | Covered (this story) |
| Opt-in keyClicks on fixture `QTextEdit` | Covered (this story) |
| Session `ui_fill(..., via_key_clicks=True)` | Covered (URL field; pre-existing) |
| Caplog `via_key_clicks=false\|true` | Covered (line edit; PYPOST-944) |
| Session body-editor keyClicks | Out of scope — fixture matches line-edit scope |
| `textChanged` multi-emit assert | Not covered — [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) |
| Per-key delay kwarg | Out of scope — [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) |
| Explicit timeout markers | **Present** — module `pytest.mark.timeout(60)` |

## Performance Concerns

None. Two isolated fixture fills add negligible CI cost (~ms each).

## Deviations from Architecture

None. Test-only change delivered as planned in `20-architecture.md`; production
module graph unchanged.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent TD-2 (plain/rich keyClicks fixtures) | This story (PYPOST-945) |
| Caplog `via_key_clicks=true` symmetry | [PYPOST-944](https://pypost.atlassian.net/browse/PYPOST-944) |
| `textChanged` multi-emit asserts | [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) |
| Per-key delay kwarg | [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) |
| Fill logging contract (production) | [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) |

### NON-BLOCKER

None new — remaining gaps are sibling stories from PYPOST-917 TD-3–TD-4.

### NON-BLOCKER follow-ups (ticketed)

| ID | Priority | Summary | Acceptance |
| --- | --- | --- | --- |
| UT-1 | Lowest | Session body-editor keyClicks smoke | `agent_e2e_session` fills request body via `via_key_clicks=True`; assert body plain text matches without live network. Jira: [PYPOST-976](https://pypost.atlassian.net/browse/PYPOST-976) |
| UT-2 | Lowest | Caplog keyClicks on plain/rich fixtures | Extend or sibling caplog test using plain/rich widget ids; assert `via_key_clicks=true` and no fill text in logs. Jira: [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977) |

### Accepted / out of scope (do not ticket)

- Live golden-flow body typing via keyClicks — fixture proof sufficient for TD-2.
- Assert full log message string on plain/rich — scalar caplog on line edit suffices.
- Native OS / IME simulation beyond Qt Test events.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** — FR1–FR4 satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — plain/rich keyClicks fixture proofs lock opt-in fill on
body-style editors; remaining items are optional sibling hardening
(PYPOST-946–947) or unticketed session/caplog extensions (UT-1–UT-2).
