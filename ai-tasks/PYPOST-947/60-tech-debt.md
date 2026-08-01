# PYPOST-947: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: optional keyword `delay: int = -1` on module + session
`ui_fill`; forwarded to `QTest.keyClicks` when `via_key_clicks=True`; default
unchanged; smoke test + Step 8 dev docs. Closes
[PYPOST-917/60-tech-debt.md](../PYPOST-917/60-tech-debt.md) TD-4.

## Shortcuts Taken

- **Mock spy for delay proof** — Asserts forwarding without positive-delay
  timing flakes in CI.
- **No delay in DEBUG logs** — Matches fill-text privacy contract; duration_ms
  reflects paced fills implicitly.
- **Setter path ignores delay** — No error when `delay` passed without
  `via_key_clicks`; simpler API.

## Code Quality Issues

None material. One extra keyword and forward call; session mirror matches
PYPOST-917 pattern.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Default fill (setter) unchanged | Covered (pre-existing) |
| keyClicks fill without explicit delay | Covered (pre-existing) |
| keyClicks fill forwards custom delay | Covered (this story) |
| Session `delay` pass-through behavioral | Covered by signature mirror; fixture smoke suffices |
| Positive-delay wall-clock assert | Out of scope — mock proof only |
| Explicit timeout markers | **Present** — module `pytestmark.timeout(60)` |

## Performance Concerns

Positive `delay` slows opt-in keyClicks fills by design; callers must opt in.
Default `-1` preserves prior CI cost.

## Deviations from Architecture

None. Delivered as planned in `20-architecture.md`.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent TD-4 (delay kwarg) | This story (PYPOST-947) |
| keyClicks fill suite | PYPOST-917 / 945 / 946 |
| Caplog fill modes | PYPOST-944 |

### NON-BLOCKER

None new — PYPOST-917 optional hardening largely closed; remaining items are
session body-editor keyClicks (PYPOST-976) and plain/rich caplog (PYPOST-977).

### Accepted / out of scope (do not ticket)

- Logging `delay` scalar on fill events.
- Validating delay range before Qt call.
- Replacing `ui_send_key` loops for paced typing.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** — FR1–FR5 + docs |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — opt-in per-key delay on keyClicks fill is implemented,
tested, and documented; closes PYPOST-917 TD-4.
