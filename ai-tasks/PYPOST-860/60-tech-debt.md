# PYPOST-860: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE (non-blockers only)

Failure artifacts meet DoD: hook + helper dump masked UI snapshot and
concise diagnostics on call failure for shared session fixtures; golden /
env-pack scenarios are covered automatically; docs describe location and
reading; secrets reuse PYPOST-835 masking. Items below are non-blocking
follow-ups.

## Shortcuts Taken

- **Auto-dump only for shared fixtures.** Tests that construct
  `AgentAppSession` directly (multi-session isolation) are not hooked;
  authors can call `dump_agent_e2e_failure_artifacts` manually.
- **No GitHub Actions upload step.** Docs describe optional
  `upload-artifact`; implementing it is follow-up debt, not DoD.
- **Exception messages truncated, not re-sanitized.** Diagnostics keep a
  short assert message; authors must not put secrets in assert text
  (existing policy). Snapshot values remain fully masked.
- **Safe nodeid dirname may collide** for extremely long / similar
  nodeids after truncation to 180 chars (unlikely in this suite).

## Code Quality Issues

- **Hook lives in the fixtures plugin** next to session fixtures — clear
  ownership, but couples packaging plugin to failure I/O (acceptable).
- **`BLE001` broad except** in dump helper is intentional best-effort;
  could narrow to `(OSError, RuntimeError, TypeError)` later.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Helper writes snapshot + diagnostics | Covered |
| Masking reused in dumped JSON | Covered |
| Best-effort on capture error | Covered |
| Hook dumps on fixture assert fail | Covered (subprocess) |
| Seeded fixture auto-dump | Implicit (same hook path); no dedicated subprocess |
| CI artifact upload | Not automated (docs only) |
| Caplog for INFO write event in hook subprocess | Not asserted (helper unit covers INFO) |

No timeout-marker blockers.

## Performance Concerns

None relative to DoD. Dump runs only on failure; success paths unchanged.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Snapshot API / masking | [PYPOST-835](https://pypost.atlassian.net/browse/PYPOST-835) |
| Env contract model | [PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) |
| Make / CI env pack entry | [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861) |

### NON-BLOCKER — need NEW Jira Debt tickets

#### Optional CI upload of agent e2e failure artifacts

- **Priority:** Low
- **Description:** When job `agent-e2e` (or main test) fails, upload
  `artifacts/agent_e2e/` via `actions/upload-artifact` so dumps are
  downloadable from the Actions UI without SSH into the runner.
- **Files:** `.github/workflows/test.yml`,
  `doc/dev/agent_e2e_failure_artifacts.md`
- **Jira:** [PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874)

#### Auto-dump for direct `AgentAppSession` constructions

- **Priority:** Low
- **Description:** Multi-session isolation tests build sessions without
  fixtures and therefore skip the hook. Consider a context manager or
  stash registry so direct constructions can opt into the same dump.
- **Files:** `tests/_pytest_plugins/agent_e2e.py`,
  `pypost/fixtures/agent_e2e_failure.py`
- **Jira:** [PYPOST-875](https://pypost.atlassian.net/browse/PYPOST-875)

#### Narrow dump helper exception types

- **Priority:** Lowest
- **Description:** Replace broad `except Exception` with a documented
  tuple (`OSError`, `RuntimeError`, `TypeError`, `ValueError`, …) once
  capture failure modes are catalogued.
- **Files:** `pypost/fixtures/agent_e2e_failure.py`
- **Jira:** [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876)
