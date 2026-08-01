# PYPOST-912: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: in-process caplog test asserts
`agent_session_failure_dump_hook_failed` when the dump hook raises; original
exception propagates; hook restored after test; module timeout marker present.
Test-only change; no production edits. No blockers.

## Shortcuts Taken

- **In-process caplog only.** Subprocess dump-file proofs retained; this ticket
  adds targeted log contract lock without re-proving artifact I/O.
- **Hardcoded event prefix + exc type.** Assert string matches production /
  `logging.md` (intentional).
- **Hook restore via plugin factory.** Uses `make_direct_session_failure_dump_hook()`
  rather than a public getter for the previous hook — adequate for agent_e2e runs.

## Code Quality Issues

- None material. Test follows sibling caplog patterns in the same module.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Hook raises → `agent_session_failure_dump_hook_failed` | Covered (this ticket) |
| Direct construction dumps on assert fail | Covered (subprocess, PYPOST-875) |
| Fixture makereport dump | Covered (subprocess) |
| Nested concurrent sessions dump selection | Not covered (unchanged) |

No timeout-marker blockers.

## Performance Concerns

One additional offscreen Qt session startup under agent e2e gate. Cost is
acceptable for optional log contract coverage.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Narrow dump helper exception types | [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876) |
| CI upload of failure artifacts | [PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874) |
| Rename `session_fixture` provenance | [PYPOST-913](https://pypost.atlassian.net/browse/PYPOST-913) |

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

**SAFE TO CLOSE** — FR1–FR4 and DoD satisfied. No new follow-ups required.
