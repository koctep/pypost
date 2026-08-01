# PYPOST-946: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: fixture test
`test_ui_fill_via_key_clicks_emits_text_changed_per_keystroke` asserts
`textChanged` emits once per keystroke on empty-start `QLineEdit` during opt-in
keyClicks fill; module green; closes
[PYPOST-917/60-tech-debt.md](../PYPOST-917/60-tech-debt.md) TD-3. No production
code changed.

## Shortcuts Taken

- **Green-on-first-run signal proof** — PYPOST-917 keyClicks fill already
  delivers per-key events; Step 3 N/A (coverage debt only).
- **Line-edit fixture only** — Plain/rich editors use no-arg `textChanged` and
  `clear()` emits once even when empty; separate counts deferred.
- **Short fill text (`"abc"`)** — Readable expected count; not the longer
  sibling fixture string.

## Code Quality Issues

None material. New test reuses `find_widget`, emission list spy, and
`try`/`finally` teardown from existing fill tests.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Opt-in keyClicks final text on fixture `QLineEdit` | Covered (pre-existing) |
| `textChanged` multi-emit on line-edit keyClicks | Covered (this story) |
| `textChanged` multi-emit on plain/rich keyClicks | Out of scope — different signal/clear semantics |
| Session body-editor keyClicks | Out of scope — [PYPOST-976](https://pypost.atlassian.net/browse/PYPOST-976) |
| Caplog keyClicks on plain/rich fixtures | Out of scope — [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977) |
| Per-key delay kwarg | Out of scope — [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) |
| Explicit timeout markers | **Present** — module `pytest.mark.timeout(60)` |

## Performance Concerns

None. One additional fixture fill adds negligible CI cost (~ms).

## Deviations from Architecture

None. Test-only change delivered as planned in `20-architecture.md`; production
module graph unchanged.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent TD-3 (textChanged multi-emit) | This story (PYPOST-946) |
| Plain/rich keyClicks fixtures | [PYPOST-945](https://pypost.atlassian.net/browse/PYPOST-945) |
| Caplog `via_key_clicks=true` symmetry | [PYPOST-944](https://pypost.atlassian.net/browse/PYPOST-944) |
| Per-key delay kwarg | [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) |
| Fill logging contract (production) | [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) |

### NON-BLOCKER

None new — remaining gaps are sibling stories from PYPOST-917 TD-4 or
PYPOST-945 UT items.

### NON-BLOCKER follow-ups (ticketed)

| ID | Priority | Summary | Acceptance |
| --- | --- | --- | --- |
| UT-1 | Lowest | Plain/rich `textChanged` multi-emit | Sibling tests on plain/rich fixtures with documented expected counts (clear + per-key). Jira: [PYPOST-980](https://pypost.atlassian.net/browse/PYPOST-980) |
| UT-2 | Lowest | Default setter single-emit contrast | Optional test: default `ui_fill` emits one `textChanged` vs multi for keyClicks. Jira: [PYPOST-981](https://pypost.atlassian.net/browse/PYPOST-981) |

### Accepted / out of scope (do not ticket)

- Asserting full emission payload sequence — count suffices for TD-3.
- Native OS / IME simulation beyond Qt Test events.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** — FR1–FR4 satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — line-edit `textChanged` multi-emit proof locks keystroke
realism on the keyClicks fill path; remaining items are optional sibling
hardening (PYPOST-947, UT-1–UT-2).
