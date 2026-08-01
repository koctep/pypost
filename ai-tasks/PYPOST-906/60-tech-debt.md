# PYPOST-906: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Preferred acceptance is met: `lint` depends on `$(VENV_MARKER) venv-test`
(mirrors `typecheck`); `run` stays marker-only; contract + bare-venv lint
smoke updated and green. Developer docs aligned in Step 8 (FR5). **Do not
create Jira tickets in this step** — Phase D skipped by orchestrator
instruction; follow-ups below are unticketed.

## Shortcuts Taken

- **Docs deferred to Step 8 (now done).** Step 8 updated
  `doc/dev/testing.md` and `doc/dev/setup.md` so lint ensures `[dev]` via
  `venv-test`; see follow-up #2 resolved and `70-dev-docs.md`.
- **No dedicated `typecheck` prereq contract test.** Lint now mirrors
  `typecheck` in the Makefile, but `tests/test_makefile.py` never asserted
  `typecheck` → `venv-test` (architecture Step 2 research overstated that
  peer lock). Out of this ticket’s DoD; optional follow-up only.
- **Full `make check` / entire suite not re-run in this review.** Step 5
  validated `make lint` + `tests/test_makefile.py` (48 passed). Sufficient
  for this one-line Make edge.

## Code Quality Issues

None that block close. Makefile change is a one-line prerequisite add;
test split (`run` vs `lint`) matches architecture. No naming / structure
debt in the edited surfaces.

## Missing Tests

| Scenario | Status |
| --- | --- |
| `lint` prereqs include marker + `venv-test` (not `install`) | Covered |
| `run` stays marker-only | Covered |
| Bare venv `make lint` succeeds via `venv-test` ensure | Covered |
| `typecheck` prereqs include marker + `venv-test` | **Not covered** — optional follow-up |
| Full `make check` after this story | Not re-run — NON-BLOCKER |

Timeout markers: module `pytestmark = pytest.mark.timeout(120)` on
`tests/test_makefile.py`; slow class `@pytest.mark.timeout(180)`. **No
timeout-marker blockers.**

## Performance Concerns

None new. First bare-venv `make lint` may pay one `venv-test` / pip
install (expected NFR3). Subsequent visits stay cheap when the
PYPOST-905 test stamp is current (NFR2).

## Follow-up Tasks

1. **Contract test: `typecheck` depends on marker + `venv-test`**
   - Priority: Low / Lowest
   - Add `test_typecheck_depends_on_marker_and_venv_test` (same shape as
     lint) so the peer pattern cannot regress silently.
   - Jira: [PYPOST-932](https://pypost.atlassian.net/browse/PYPOST-932)

2. **Stale developer docs beyond Step 8 primary files (if any remain)**
   - Priority: Lowest
   - **Resolved (Step 8 completed):** `doc/dev/testing.md` and
     `doc/dev/setup.md` now document lint → `venv-test` ensure; contract
     table no longer says bare venv fails lint; `run` stays marker-only.
     See `ai-tasks/PYPOST-906/70-dev-docs.md`.
   - No additional product/README footguns found outside those paths in
     the Step 7 review. Historical ai-tasks prose left as point-in-time.
   - Jira: [PYPOST-932](https://pypost.atlassian.net/browse/PYPOST-932)
     (docs owned by Step 8 of this ticket, not a separate Debt)

## Blocker Verdict

**SAFE TO CLOSE** — acceptance criteria for ensure-tooling met (`lint` →
`venv-test`; tests green; `run` unchanged). Docs pending Step 8 are not a
blocker for Step 7 debt-analysis close. No merge/release blockers.
