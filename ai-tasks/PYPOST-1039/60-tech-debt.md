# PYPOST-1039: Technical Debt Analysis

## Review Verdict

**SAFE TO CLOSE — the previously recorded HTTPS transport and changed-test
lint blockers are fixed and independently re-reviewed.**

The live-smoke boundary is otherwise intentionally narrow: it loads exactly
four allowlisted read-only requests, keeps normal PR jobs free of Jira
configuration, and limits the protected workflow to manual dispatch in the
`jira-live-smoke` environment.  The absent-opt-in target also exits cleanly as
an intentional skip.

## Shortcuts Taken

- None accepted. The smoke is deliberately limited to a four-operation
  read-only contract rather than trying to validate the whole Jira MCP
  collection.
- The protected CI job reports only a fixed pass / failed / intentionally
  skipped summary, instead of test output or Jira-derived data.

## Code Quality Issues

- Resolved — the changed test modules pass direct `flake8` validation. The
  prior `E501` in `tests/test_jira_mcp_live_smoke.py` was wrapped; no changed
  test-module lint finding remains.
- Resolved — `_live_smoke_configuration` now accepts a valid `https` URL only.
  It rejects `http`, other schemes, malformed URLs, URLs with credentials, and
  whitespace-bearing URLs through the same fixed, value-free configuration
  failure. Credentials therefore cannot be injected into the protected smoke
  request template when its configured transport is plaintext.

## Missing Tests

- Resolved — the deterministic enabled-configuration matrix includes an
  `http://` base URL and asserts only the fixed generic configuration failure,
  preventing a relaxation of the HTTPS gate.
- Existing task test modules carry explicit timeout markers; no timeout debt
  was found.

## Performance Concerns

- None. The authorized run performs four sequential, bounded MCP calls and is
  excluded from ordinary local and PR validation.

## Follow-up Tasks

- None. The two release blockers were resolved within PYPOST-1039; no deferred
  Jira debt item is required.

## Validation Evidence

- `env -u PYPOST_LIVE_JIRA_SMOKE -u JIRA_BASE_URL -u JIRA_CREDENTIALS -u
  JIRA_PROJECT_KEY make test-jira-mcp-live`: intentionally skipped, successful
  exit, and no live Jira configuration consumed.
- `PYTEST_ARGS='tests/test_jira_mcp_live_smoke.py
  tests/test_example_fixtures.py' make test`: 19 passed, 1 deselected.
- Direct `flake8` of `tests/test_jira_mcp_live_smoke.py` and
  `tests/test_example_fixtures.py`: passed after the wrapped assertion.
- Independent re-review inspected the HTTPS-only validation, the deterministic
  plaintext-URL rejection test, the changed-test lint result, the read-only
  allowlist, secret gate, logging suppression, Make target, and dispatch-only
  protected CI boundary. No release blocker remains.
