# PYPOST-966: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Added post-install `pypost.version.__version__` read to slow smoke via shared
`POST_INSTALL_SANITY_SNIPPETS` and `_assert_post_install_sanity`. Resolves PYPOST-943 TD-4.
Changes are test helpers and a fast contract guard only — no application or CI workflow edits.

## Shortcuts Taken

- **Version-module read, not bare `import pypost`.** Safer if `pypost/__init__.py` later
  re-exports UI modules; still satisfies “package importability” acceptance.
- **Slow smoke not re-run locally in Step 5.** Network-heavy; contract guard + code review
  cover snippet wiring; CI `make-install-smoke` is integration signal.

## Code Quality Issues

None remaining for this task scope.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Post-install pydantic import (PYPOST-559) | Covered — first snippet |
| Post-install pypost version read | Covered — second snippet in slow smoke |
| Snippet policy cannot regress silently | Covered — `test_post_install_sanity_includes_pypost_version_read` |
| Live GitHub Actions `make-install-smoke` green proof | CI job is integration signal |

## Performance Concerns

None. One additional subprocess in slow smoke (negligible vs pip install).

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Revisit post-install snippet if `pypost/__init__.py` gains eager UI imports | Version-module read avoids today; bare import would not | [PYPOST-1014](https://pypost.atlassian.net/browse/PYPOST-1014) |

## Blocker review

**No blockers.** Snippet list includes pypost version read; contract test green; pydantic
check preserved. Safe to close.
