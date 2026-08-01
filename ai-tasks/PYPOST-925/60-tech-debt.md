# PYPOST-925: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE (Step 8 dev-docs light touch remains; no blockers)

Strengthened the Qt/EGL CI contract so `_expected_qt_egl_packages()` derives the
expected set solely from `.github/actions/install-qt-egl-runtime/action.yml`.
Removed `_PEER_QT_EGL_PACKAGES` and frozenset-gated parsing. Resolves TD-2 from
PYPOST-923/924. Eight workflow-contract tests pass with explicit timeout markers.
No product-code changes.

**Do not create Jira tickets in this step** — Phase D / tech-debt sync fills the
Jira column later.

## Shortcuts Taken

- **`libegl1` as inline-install sentinel.** `test_workflow_has_zero_inline_libegl1_apt_install_blocks`
  detects duplicated inline apt blocks only when `libegl1` appears in the run body.
  Sufficient for the current Qt/EGL package set; a hypothetical inline install that
  omitted `libegl1` would not be caught (unlikely for headless PySide6 provisioning).
- **Structural sanity without explicit eight-package frozenset.** Non-empty derived set
  plus `libegl1` sentinel replaces the hardcoded eight-name gate. Removing a non-sentinel
  package from `action.yml` would not fail the contract until CI collection/runtime
  breaks — acceptable trade-off per architecture (single edit point in composite).
- **Heuristic apt-line parser retained.** `_packages_from_apt_install_block` scans
  continuation lines with a Debian name regex rather than parsing YAML structure (same
  pattern as PYPOST-923/924; TD-5 deferred).
- **Neutral reference helper for introspection tests.** `_reference_packages_from_composite_action`
  duplicates the composite read path intentionally so red/green tests can compare
  `_expected_qt_egl_packages()` against a test-local reference without importing
  private implementation details.

## Code Quality Issues

- **Partial overlap between composite validation tests.**
  `test_install_qt_egl_composite_action_exists_with_full_package_set` and
  `test_composite_qt_egl_packages_inherited_by_qt_using_jobs` both assert non-empty
  derived set and `libegl1` presence. The latter adds headless-runtime context in
  error messages; consolidation is optional cosmetic debt.
- **YAML job-block parsing remains heuristic.** `_job_block` and
  `_count_inline_libegl1_apt_install_blocks` use indentation and regex heuristics
  (shared fragility with PYPOST-874 / PYPOST-923 / PYPOST-924). TD-5 / PYPOST-928.
- **Module filename still smoke-centric.** `test_ci_make_install_smoke_qt_runtime.py`
  predates three-job equal-weight coverage; rename would churn imports/docs (low
  priority).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Composite exists with derived package set + `libegl1` | Covered (`test_install_qt_egl_composite_action_exists_with_full_package_set`) |
| All three Qt jobs reference composite `uses:` | Covered (`test_qt_using_jobs_reference_install_qt_egl_composite`) |
| Zero inline libegl1 apt install blocks in workflow | Covered (`test_workflow_has_zero_inline_libegl1_apt_install_blocks`) |
| Inherited composite package integrity for Qt-using jobs | Covered (`test_composite_qt_egl_packages_inherited_by_qt_using_jobs`) |
| `make-install-smoke` job exists | Covered (`test_make_install_smoke_job_exists`) |
| No `_PEER_QT_EGL_PACKAGES` module attribute | Covered (`test_qt_egl_contract_has_no_duplicate_authoritative_frozenset`) |
| Derived-only `_expected_qt_egl_packages()` | Covered (`test_expected_qt_egl_packages_derived_from_composite_only`) |
| Validation tests call derived helper | Covered (`test_composite_validation_uses_derived_package_helper`) |
| Explicit timeout markers on contract module | Covered (`pytestmark = pytest.mark.timeout(10)`) |
| Composite step ordered before `setup-python` in each job | Not covered — relies on workflow review and CI collection success |
| Live GitHub Actions proof of apt + PySide6 collection | Not covered — CI jobs are the integration signal |
| Lazy conftest Qt import without apt | Out of scope — see TD-3 |

**No timeout-marker blockers.**

## Performance Concerns

None introduced. Contract tests remain pure filesystem reads and module introspection
(≤10s module timeout). No change to CI apt provisioning wall-clock.

## Resolved by This Ticket

| ID | Source | Resolution |
| -- | ------ | ---------- |
| TD-2 | PYPOST-923 / PYPOST-924 | Expected package set derived from composite `action.yml` only; `_PEER_QT_EGL_PACKAGES` removed |
| Smoke-centric peer framing | PYPOST-924 debt | Renamed/refocused inherited-package test; three-job `uses:` coverage unchanged in sibling test |

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-3 | Lowest | Optionally defer `PySide6` import in `tests/conftest.py` so non-GUI collection paths do not require EGL/GL system libs | Explicitly out of scope for 925; reduces env coupling for future jobs | [PYPOST-926](https://pypost.atlassian.net/browse/PYPOST-926) |
| TD-5 | Lowest | Harden workflow YAML parsing helpers shared by CI contract tests (or adopt a tiny YAML subset parser) | Shared fragility across PYPOST-874-style tests | [PYPOST-928](https://pypost.atlassian.net/browse/PYPOST-928) |
| TD-925-1 | Lowest | Optionally consolidate overlapping composite sanity tests or rename module file away from smoke-centric naming | Cosmetic; no functional gap | — (unticketed; sync if desired) |
| TD-925-2 | Lowest | Step 8: remove dual-edit maintainer guidance from `doc/dev/setup.md` and `doc/dev/testing.md` | Planned Step 8 scope | — (this sprint task) |

### Already tracked / do not reticket as new work from this file alone

| Area | Owner / note |
| --- | --- |
| Production lock CI `check-lock` job | [PYPOST-927](https://pypost.atlassian.net/browse/PYPOST-927) (PYPOST-923 TD-4) |
| Workflow contract-test precedent | PYPOST-861 / PYPOST-874 / PYPOST-923 / PYPOST-924 |
| Parent consolidation | [PYPOST-924](https://pypost.atlassian.net/browse/PYPOST-924) |

## User documentation

N/A for end-user `doc/user/` — CI contract hygiene only. Step 8 will update
`doc/dev/setup.md` and `doc/dev/testing.md` to document single-edit workflow in
`action.yml` only.

## Blocker review

**No blockers.** Timeout markers present; eight contract tests green; FR1–FR6 and
Definition of Done satisfied for contract scope. Step 8 dev-docs remain before full
task closure in the top-down workflow.

## Worklog

tokens_used: (subagent aggregate)
role: execution
step: 7
step_name: Review and Technical Debt
