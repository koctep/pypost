# PYPOST-274: Technical Debt Analysis

## Shortcuts Taken

No shortcuts or temporary workarounds. Tests use real GNU Make in isolated workspaces rather than
mocking subprocess behavior.

## Code Quality Issues

No major code quality issues. Helpers (`_run_make`, `_prerequisites`, `_seed_minimal_project`)
are shared across test classes and mirror patterns in `tests/test_pytest_exit_policy.py`.

## Missing Tests

Remaining gaps are **non-blocking** follow-ups:

| Scenario | Severity | Notes |
| --- | --- | --- |
| `make run` success path | Low | Needs full `pypost/main.py` and Qt bootstrap in fixture |
| `make test-cov` execution | Low | Prerequisite chain is tested; recipe smoke not run (slower) |
| `make test-slow` target wiring | Low | Slow class runs via `-m slow`; Make target itself not invoked |

All acceptance criteria from PYPOST-274 and PYPOST-277 are covered.

## PYPOST-277 closure

[PYPOST-277](https://pypost.atlassian.net/browse/PYPOST-277) requested a lightweight automation
suite for `venv`, `install`, `test`, and `lint` exit codes. That scope is implemented in
`TestTargetExecution` and related dependency/exit classes within `tests/test_makefile.py`:

| PYPOST-277 requirement | Test coverage |
| --- | --- |
| `venv` / marker bootstrap | `TestMarkerLifecycle`, `test_venv_test_installs_pytest_and_flake8` |
| `install` succeeds | `test_install_succeeds_with_empty_requirements` |
| `test` after install | `test_test_succeeds_after_install`, `test_make_test_excludes_slow_marker` |
| `lint` after install | `test_lint_succeeds_after_install` |
| Bare venv failures | `test_test_fails_without_pytest_in_bare_venv`, `test_lint_fails_without_flake8_in_bare_venv` |

**Verdict:** PYPOST-277 is satisfied by this change set; no separate follow-up issue required.

## Performance Concerns

Fast suite (~45s locally) runs 18 cases excluding `@pytest.mark.slow`. Slow install smoke
remains opt-in via `make test-slow` or `pytest -m slow` to avoid network cost in default CI.

## Follow-up Tasks

| Item | Jira | Priority |
| --- | --- | --- |
| Optional `make test-cov` recipe smoke | — | Low (create Debt if desired) |
| Optional `make run` smoke in fixture | — | Low |
| CI install caching | [PYPOST-278](https://pypost.atlassian.net/browse/PYPOST-278) | Existing debt |
| Flake8 baseline cleanup | [PYPOST-280](https://pypost.atlassian.net/browse/PYPOST-280) | Existing debt |

No blockers. **SAFE TO CLOSE** for PYPOST-274 and PYPOST-277.
