# PYPOST-924: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Consolidated the Qt/EGL apt install into a local composite action consumed by
`test`, `make-install-smoke`, and `agent-e2e`. Resolves [PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923)
TD-1 (triple inline YAML copy). Five workflow-contract tests pass with explicit
timeout markers. No product-code changes.

**Do not create Jira tickets in this step** — Phase D / tech-debt sync fills the
Jira column later.

## Shortcuts Taken

- **Dual package definition (composite + test frozenset).** Package names live in
  `.github/actions/install-qt-egl-runtime/action.yml` and again in
  `_PEER_QT_EGL_PACKAGES` in `tests/test_ci_make_install_smoke_qt_runtime.py`.
  The contract module cross-checks them; a package change still requires editing
  two places until TD-2 (PYPOST-925) derives the expected set from the composite
  alone. Acceptable per architecture scope (“no cross-job frozenset derivation”).
- **`libegl1` as inline-install sentinel.** `test_workflow_has_zero_inline_libegl1_apt_install_blocks`
  detects duplicated inline apt blocks only when `libegl1` appears in the run body.
  Sufficient for the current eight-package set; a hypothetical inline install that
  omitted `libegl1` would not be caught (unlikely for Qt/EGL provisioning).
- **First local composite under `.github/actions/`.** No repo-wide composite
  conventions (inputs, branding, shared shell helpers) were established; this
  action is minimal by design.

## Code Quality Issues

- **Hardcoded frozenset remains the canonical expected set in tests.** Even after
  consolidation, `_PEER_QT_EGL_PACKAGES` is the gate; maintainers must keep it in
  sync with `action.yml` (TD-2 / PYPOST-925).
- **YAML job-block parsing is heuristic.** `_job_block`, `_apt_packages_in_block`,
  and `_count_inline_libegl1_apt_install_blocks` use indentation and token
  heuristics (same class as PYPOST-874 / PYPOST-923). Brittle if workflow layout
  changes radically (TD-5 / PYPOST-928).
- **Peer parity test still emphasizes smoke vs `agent-e2e`.**
  `test_make_install_smoke_has_full_peer_qt_egl_apt_set` asserts composite
  `uses:` on smoke and `agent-e2e` plus composite package set; the `test` matrix
  job is covered by `test_qt_using_jobs_reference_install_qt_egl_composite` but
  not by an explicit smoke-style peer frozenset check on its job block (TD-2).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Composite exists with eight-package set | Covered (`test_install_qt_egl_composite_action_exists_with_full_package_set`) |
| All three Qt jobs reference composite `uses:` | Covered (`test_qt_using_jobs_reference_install_qt_egl_composite`) |
| Zero inline libegl1 apt install blocks in workflow | Covered (`test_workflow_has_zero_inline_libegl1_apt_install_blocks`) |
| Smoke peer parity via composite package set | Covered (`test_make_install_smoke_has_full_peer_qt_egl_apt_set`) |
| `make-install-smoke` job exists | Covered (`test_make_install_smoke_job_exists`) |
| Explicit timeout markers on contract module | Covered (`pytestmark = pytest.mark.timeout(10)`) |
| Composite step ordered before `setup-python` in each job | Not covered — relies on workflow review and CI collection success |
| Live GitHub Actions proof of apt + PySide6 collection | Not covered — CI jobs are the integration signal |
| Derive expected packages solely from `action.yml` (no frozenset) | Not implemented — see TD-2 |
| Lazy conftest Qt import without apt | Out of scope — see TD-3 |

**No timeout-marker blockers.**

## Performance Concerns

None introduced. Each Qt-using job still runs one `apt-get update` + install
sequence per job invocation (same wall-clock class as pre-924 inline steps).
Composite indirection adds negligible Actions overhead.

## Resolved by This Ticket

| ID | Source | Resolution |
| -- | ------ | ---------- |
| TD-1 | PYPOST-923 | Shared composite at `.github/actions/install-qt-egl-runtime`; three inline blocks removed from `test.yml` |

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-2 | Low | Strengthen Qt contract: derive expected package set from composite `action.yml` only (and/or assert all three job blocks share identical provisioning) instead of maintaining `_PEER_QT_EGL_PACKAGES` separately | Reduces dual-edit burden when packages change; remainder / peer equality | [PYPOST-925](https://pypost.atlassian.net/browse/PYPOST-925) |
| TD-3 | Lowest | Optionally defer `PySide6` import in `tests/conftest.py` so non-GUI collection paths do not require EGL/GL system libs | Explicitly out of scope for 924; reduces env coupling for future jobs | [PYPOST-926](https://pypost.atlassian.net/browse/PYPOST-926) |
| TD-5 | Lowest | Harden workflow YAML parsing helpers shared by CI contract tests (or adopt a tiny YAML subset parser) | Shared fragility with PYPOST-874-style tests | [PYPOST-928](https://pypost.atlassian.net/browse/PYPOST-928) |

### Already tracked / do not reticket as new work from this file alone

| Area | Owner / note |
| --- | --- |
| Production lock CI `check-lock` job | [PYPOST-927](https://pypost.atlassian.net/browse/PYPOST-927) (PYPOST-923 TD-4) |
| Workflow contract-test precedent | PYPOST-861 / PYPOST-874 / PYPOST-923 |
| Parent consolidation debt | [PYPOST-924](https://pypost.atlassian.net/browse/PYPOST-924) closes PYPOST-923 TD-1 |

## User documentation

N/A for end-user `doc/user/` — CI workflow hygiene only. Step 8 updated
`doc/dev/setup.md` and `doc/dev/testing.md` to name the composite path (see
`ai-tasks/PYPOST-924/70-dev-docs.md`).

## Blocker review

**No blockers.** Timeout markers present; five contract tests green; architecture
decisions (composite action, eight-package parity, three-job coverage) met.
Definition of Done satisfied.

## Worklog

tokens_used: (subagent aggregate)
role: execution
step: 7
step_name: Review and Technical Debt
