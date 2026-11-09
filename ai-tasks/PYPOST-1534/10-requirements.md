# PYPOST-1534: HTTP client blank path segment rejection vs test_http_client

## Goals

Restore a correct, trustworthy contract between HTTP path-segment safety rules and the
HTTP client test suite so quality gates fail only on real product defects.

After PYPOST-1332 extended fail-closed blank path-segment rejection (related to
PYPOST-1346 `.` / `..` sanitization), many `tests/test_http_client.py` cases began failing
with `blank_path_segment_rejected` on ordinary origin-only URLs used as fixtures
(e.g. `http://x`). Triage classified this as pre-existing NON-BLOCKER debt
([PYPOST-1534](https://pypost.atlassian.net/browse/PYPOST-1534)).

**Business reason (mandatory):** Operators and developers must keep intentional security
behavior (reject dangerous blank mid-path / trailing segments that can hit the wrong
endpoint) while still allowing legitimate requests that simply have **no path** after the
host. Otherwise the suite is red for the wrong reason, CI signal is noisy, and the
product appears to reject valid URLs that have always been legal HTTP.

Prefer product correctness: blank *segments* remain rejected; empty *path* (no segments)
must remain allowed. Tests that intentionally probe blank-segment rejection stay as
security regression coverage; fixture URLs without a path must work without being rewritten
solely to paper over an over-broad guard.

**Implementation language:** Python

## User Stories

- As a **developer** running `make test` on HTTP client coverage, I want origin-only and
  other empty-path fixture URLs to prepare and dispatch normally, so unrelated HTTP client
  behavior stays testable.
- As a **security-conscious product owner**, I want mid-path `//` and trailing blank path
  segments to keep failing closed before dispatch, so empty template variables cannot
  silently hit a different same-host endpoint.
- As a **CI / release operator**, I want `tests/test_http_client.py` to pass when product
  behavior matches the documented path-safety contract, so blank-segment guardrails do not
  masquerade as broad suite breakage.

## Definition of Done

1. **Empty path allowed**: A rendered request URL whose path component is empty (no `/`
   after the authority, e.g. `http://example.test`) prepares and may dispatch; it is not
   treated as a blank path segment.
2. **Blank segments still rejected**: Mid-path empty segments (`…//…`) and trailing blank
   segments (`…/projects/`) still raise a TEMPLATE execution error before `session.request`,
   with existing blank-path wording and logging behavior retained.
3. **Dot rejection retained**: Whole-segment `.` / `..` rejection from PYPOST-1346 remains
   unchanged.
4. **Suite green for HTTP client**: `make test PYTEST_ARGS='tests/test_http_client.py'`
   passes (including blank-segment rejection cases and ordinary fixture URLs).
5. **Make-only verification**: Confirmation uses repository Make targets only.
6. **Docs aligned**: Developer docs that describe blank-segment policy explicitly distinguish
   empty path from blank segments.

## Task Description

### Problem

PYPOST-1332 intentionally rejects blank path *segments* after URL render so empty path
variables cannot produce ambiguous URLs. The shared guard incorrectly treats an **empty
path** (common in fixture and host-only URLs) as a blank segment, raising
`ExecutionError` / logging `blank_path_segment_rejected` for URLs such as `http://x`.

That breaks dozens of `tests/test_http_client.py` cases that never intended to exercise
blank-segment security; they only needed a simple base URL.

### Scope (in)

- Clarify and enforce: empty path ≠ blank segment.
- Keep intentional blank-segment and `.` / `..` fail-closed behavior.
- Add / adjust automated coverage that proves empty-path URLs still prepare.
- Update developer documentation for the path-segment rejection contract.
- Verify with `make test` scoped to `tests/test_http_client.py`.

### Scope (out)

- Changing MCP collection templates or GitHub/GitLab blank-arg offline cases (already
  covered; should remain green).
- Percent-encoded lookalikes (`%2e`) — remaining debt under PYPOST-1346 notes.
- Renaming `_assert_no_dot_path_segments` (cosmetic debt from PYPOST-1332).
- Committing or transitioning the Jira issue (orchestrator / parent owns that).

## Constraints and Assumptions

- Blank-segment rejection is intentional security behavior (PYPOST-1332); do not remove it.
- Prefer fixing the product guard over rewriting every fixture URL to include a dummy path.
- Make-only workflow; Jira-driven scope limited to this Debt issue (3 SP).

## Main Entities

- **Rendered request URL**: Final URL string after template render, before HTTP dispatch.
- **Path segment**: Piece of the URL path between `/` separators.
- **Empty path**: Path component with no characters (host-only / origin-style URL).
- **Blank segment**: An empty piece inside a non-empty path (`//` or trailing `/`).
- **HTTP client prepare seam**: Shared pre-dispatch validation that fail-closes unsafe paths.

## Q&A

| Question | Answer |
| -------- | ------ |
| Should tests be updated to expect blank rejection on `http://x`? | No — that would encode incorrect product behavior. Empty path is valid HTTP. |
| Is blank mid-path / trailing rejection still desired? | Yes — keep PYPOST-1332 fail-closed semantics. |
| Related history? | PYPOST-1346 (`.` / `..`); PYPOST-1332 (blank segments); triage debt PYPOST-1534. |
