# PYPOST-905: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Option B stamp files for `venv-test` / `venv-otel` land in the root
`Makefile`; `install` touches both stamps; contract tests cover skip /
install-when-needed / stamp prereqs. Items below are non-blocking.
**Do not create Jira tickets in this step** — list unticketed follow-ups
for the orchestrator (Phase D).

## Shortcuts Taken

- **Stamp invalidation keys on `pyproject.toml` (+ marker only).**
  Editing `requirements-dev.in` / lock files without bumping
  `pyproject.toml` extras will not refresh stamps. Accepted: extras
  declarations live in `pyproject.toml`; lock drift is a separate
  workflow (`make lock-dev` / CI check-lock).
- **No behavioral assert that `make install` creates/touches both
  stamps.** Architecture requires the touch; recipe is present. A
  dedicated contract test was deferred (see follow-ups).
- **Full `make check` / entire suite not re-run.** Validated
  `make lint` + `tests/test_makefile.py` (48 passed).

## Code Quality Issues

- None that block close. Optional: assert `install` stamp touch in
  `tests/test_makefile.py`.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Skip pip when stamp current (`venv-test` / `venv-otel`) | Covered |
| Install when stamp missing / stale | Covered |
| Alias depends on stamp; stamp depends on marker + pyproject | Covered |
| Pytest targets still depend on `venv-test` / `venv-otel` | Covered |
| `make install` touches both stamp files | Not covered — follow-up |
| Full `make check` after this story | Not re-run — NON-BLOCKER |

Timeout markers: module `pytestmark` on `test_makefile.py`. **No
timeout-marker blockers.**

## Performance Concerns

- First visit still pays normal pip time (expected). Subsequent visits
  with current stamps skip pip (goal of this ticket).
- Stale `pyproject.toml` mtime (e.g. accidental `touch`) forces
  reinstall — acceptable Make semantics.

## Follow-Up Tasks

1. **Contract test: `make install` touches both extra stamps**
   - Priority: Low
   - After `make install` in the makefile workspace fixture, assert
     `.venv/.venv-test-<pyver>` and `.venv/.venv-otel-<pyver>` exist
     (and optionally that a following `venv-test` / `venv-otel` skips
     pip).
   - Jira: [PYPOST-929](https://pypost.atlassian.net/browse/PYPOST-929)

2. **Optional: `lint` depend on `venv-test`**
   - Priority: Lowest
   - Out of scope here; tracked separately.
   - Jira: [PYPOST-906](https://pypost.atlassian.net/browse/PYPOST-906)

## Blocker Verdict

**SAFE TO CLOSE** — acceptance criteria met; no blockers relative to
DoD. Docs updates in Step 8 close FR6.
