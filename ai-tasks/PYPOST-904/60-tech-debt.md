# PYPOST-904: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: marked `agent_e2e` env Send smoke asserts
`agent_e2e_http_stub_installed name=seed_get_ok` under caplog on the live GUI
path (stub CM + Send click + settle), not unit-only CM enter. Module timeout
marker present. No production changes; no blockers.

## Shortcuts Taken

- **Single GUI scenario.** Only seed GET env Send extended; seed POST and
  mapping multi-URL Sends remain covered by behavioral tests without install
  caplog re-assert (optional siblings).
- **Dual coverage with PYPOST-870 / 903.** Pure-unit matrix remains the fast
  exhaustive name-token path; this ticket adds one live offscreen re-assert.
- **Hardcoded event prefix.** Assert string matches production / `logging.md`
  (intentional).

## Code Quality Issues

- None material. Smoke follows PYPOST-899 live caplog + env Send settle style.
- Sibling test avoids bloating the original FR4 Send test.

## Missing Tests

| Scenario | Status |
| --- | --- |
| GUI env GET Send → `name=seed_get_ok` caplog | Covered (this ticket) |
| Unit matrix all name tokens (PYPOST-903) | Covered (sibling module) |
| GUI seed POST Send install caplog | Not covered (optional) |
| GUI mapping multi-URL install caplog | Not covered (optional) |

No timeout-marker blockers.

## Performance Concerns

One additional offscreen Send under `make test-agent-e2e` for the env module.
Cost acceptable for optional e2e confidence.

## Follow-up Tasks

### Already tracked (do not reticket)

None. Parent optional items (PYPOST-870 name matrix, PYPOST-903 unit matrix)
are closed.

### NON-BLOCKER

None new from this ticket.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None — test-only as planned |
| Hardcoded values | Event prefix intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR5 and DoD satisfied. No new follow-ups required.
