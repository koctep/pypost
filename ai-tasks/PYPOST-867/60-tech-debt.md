# PYPOST-867: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: blank and seeded packaging fixtures emit
`agent_e2e_fixture_ready` under caplog; module timeout marker present.
No production changes; no blockers.

## Shortcuts Taken

- **Mocked session boundary.** Proofs patch `AgentAppSession` and
  `seeded_agent_dirs` instead of driving a live offscreen Qt session. Matches
  architecture (fast unit) and still executes the fixture generators'
  log lines.
- **Private pytest unwrap API.** Tests call
  `FixtureFunctionDefinition._get_wrapped_function()` to drive yield fixtures
  outside a request. Stable on pytest 8.4.x used here; may need a tweak if
  pytest internals change.
- **Hardcoded event prefixes.** Assert strings match production /
  `logging.md` (intentional).

## Code Quality Issues

- None material. Module follows sibling packaging/caplog style (862/860).
- Dedicated pure-unit module (no `agent_e2e` marker) keeps proofs out of the
  harness table — intentional.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Blank ready → `agent_e2e_fixture_ready mode=blank` | Covered (this ticket) |
| Seeded ready → `agent_e2e_fixture_ready mode=seeded` | Covered (this ticket) |
| Live GUI path re-assert of same events | Not covered (optional; mocked path sufficient for AC) |

No timeout-marker blockers.

## Performance Concerns

None. Mocked unit tests are sub-millisecond; no GUI session.

## Follow-up Tasks

### Already tracked (do not reticket)

None specific to this packaging-ready caplog debt beyond the closed parent
[PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858) item that spawned
this ticket.

### NON-BLOCKER

#### Optional live-session ready-log smoke

- **Priority:** Lowest
- **Description:** One offscreen `agent_e2e_session` / seeded test that
  asserts the same ready events without mocking, for end-to-end log
  confidence.
- **Remediation:** Add a thin marked `agent_e2e` test or extend an existing
  lifecycle smoke with caplog (cost: Qt session time).
- **Jira:** [PYPOST-899](https://pypost.atlassian.net/browse/PYPOST-899)

#### Optional public fixture-drive helper

- **Priority:** Lowest
- **Description:** If more packaging unit tests need to drive yield fixtures,
  wrap `_get_wrapped_function` in a small test helper to isolate pytest API
  churn.
- **Remediation:** `tests/helpers/` helper used by packaging log tests.
- **Jira:** [PYPOST-900](https://pypost.atlassian.net/browse/PYPOST-900)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(30)` |
| Deviations from architecture | None — test-only as planned |
| Hardcoded values | Event prefixes intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR4 and DoD satisfied. Remaining items are optional
live-path / helper polish, not blockers (ticketed as PYPOST-899 / PYPOST-900).
