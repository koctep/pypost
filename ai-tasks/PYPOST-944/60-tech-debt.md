# PYPOST-944: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: parametrized `test_ui_action_applied_caplog` asserts
`via_key_clicks=true` and `via_key_clicks=false` on DEBUG `ui_action_applied`,
fill text absent from caplog, module green (28 passed); closes
[PYPOST-917/60-tech-debt.md](../PYPOST-917/60-tech-debt.md) TD-1. No
production code changed.

## Shortcuts Taken

- **Green-on-first-run caplog proof** — PYPOST-917 already emits
  `via_key_clicks=true`; Step 3 N/A (coverage debt only).
- **Parametrize vs sibling test** — Single test over `(False, "false")` and
  `(True, "true")` per architecture preference (DRY, FR5).
- **Fixture-only caplog** — Matches false-path scope; session fill stays
  behavioral-only (requirements out of scope).
- **`import logging` inside test** — Matches existing caplog test style in
  module; no module-level import churn.

## Code Quality Issues

None material. Parametrization reuses `_make_fixture`, scoped logger caplog,
`ui_action_applied` record filter, and `try`/`finally` teardown from
PYPOST-851 false-path pattern.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Caplog `via_key_clicks=false` + no fill text | Covered (parametrize) |
| Caplog `via_key_clicks=true` + no fill text | Covered (parametrize) |
| Default fill behavior on fixture | Covered (pre-existing) |
| Opt-in keyClicks on fixture | Covered (pre-existing) |
| Session `ui_fill(..., via_key_clicks=True)` | Covered (behavioral) |
| Session caplog for opt-in fill | Out of scope — fixture matches false-path |
| KeyClicks on `QPlainTextEdit` / `QTextEdit` | Not covered — [PYPOST-945](https://pypost.atlassian.net/browse/PYPOST-945) |
| `textChanged` multi-emit assert | Not covered — [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) |
| Per-key delay kwarg | Out of scope — [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) |
| Explicit timeout markers | **Present** — module `pytest.mark.timeout(60)` |

## Performance Concerns

None. Caplog parametrization adds one fast fixture fill case (~1 ms).

## Deviations from Architecture

None. Test-only change delivered as planned in `20-architecture.md`; production
module graph unchanged.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent TD-1 (caplog `via_key_clicks=true`) | This story (PYPOST-944) |
| KeyClicks on plain/rich text editors | [PYPOST-945](https://pypost.atlassian.net/browse/PYPOST-945) |
| `textChanged` multi-emit asserts | [PYPOST-946](https://pypost.atlassian.net/browse/PYPOST-946) |
| Per-key delay kwarg | [PYPOST-947](https://pypost.atlassian.net/browse/PYPOST-947) |
| Fill logging contract (production) | [PYPOST-917](https://pypost.atlassian.net/browse/PYPOST-917) |

### NON-BLOCKER

None new — remaining gaps are sibling stories from PYPOST-917 TD-2–TD-4.

### Accepted / out of scope (do not ticket)

- Live `agent_e2e_session` caplog for opt-in fill — requirements explicitly
  defer to fixture proof.
- Separate sibling test for true path — parametrization chosen per architecture.
- Assert full log message string — scalar substring checks match false-path
  precedent.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** — FR1–FR5 satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — symmetric fill caplog proof locks the DEBUG
`via_key_clicks` scalar for both modes; remaining gaps are optional sibling
hardening (PYPOST-945–947).
