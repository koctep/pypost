# PYPOST-899: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: thin marked `agent_e2e` live-session smokes assert blank and
seeded `agent_e2e_fixture_ready` under caplog without mocking the session
boundary; module timeout marker present; harness table synced. No production
changes; no blockers.

## Shortcuts Taken

- **Dual coverage with PYPOST-867.** Mocked unit proofs remain the fast path;
  this ticket adds live offscreen re-assert only for end-to-end log confidence.
- **`getfixturevalue` caplog pattern.** Drives fixtures inside caplog block so
  setup logs are captured; slightly non-obvious but stable pytest idiom.
- **Hardcoded event prefixes.** Assert strings match production /
  `logging.md` (intentional).

## Code Quality Issues

- None material. Module follows sibling live smoke style (lifecycle_smoke).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Live blank ready → `agent_e2e_fixture_ready mode=blank` | Covered (this ticket) |
| Live seeded ready → `agent_e2e_fixture_ready mode=seeded` | Covered (this ticket) |
| Mocked unit ready caplog (PYPOST-867) | Covered (sibling module) |

No timeout-marker blockers.

## Performance Concerns

Live smokes add two offscreen Qt session startups under `make test-agent-e2e`.
Cost is acceptable for optional e2e confidence; default `make test` includes
agent_e2e via `-m "not slow"` so these run in CI agent-e2e gate.

## Follow-up Tasks

### Already tracked (do not reticket)

- Optional public fixture-drive helper — [PYPOST-900](https://pypost.atlassian.net/browse/PYPOST-900)

### NON-BLOCKER

None new from this ticket.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None — test-only as planned |
| Hardcoded values | Event prefixes intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR4 and DoD satisfied. No new follow-ups required.
