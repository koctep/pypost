# PYPOST-1534: Technical Debt Analysis

## Shortcuts Taken

- **Minimal helper branch only.** Fixed empty-path over-reject with an early return on
  `path == ""` rather than restructuring segment iteration or renaming the helper.
- **No collection-suite re-audit.** Relied on existing GitHub/GitLab blank-path offline
  tests plus full `tests/test_http_client.py` green; did not expand representative MCP
  coverage in this ticket.

## Code Quality Issues

- **Helper name mismatch** (`_assert_no_dot_path_segments` also enforces blanks and
  empty-path allow). Cosmetic rename to `_assert_safe_path_segments` remains deferred
  (PYPOST-1332 debt); not re-filed.
- **Event selection via detail string prefix** (`Blank path segment`) unchanged; still
  couples log event naming to exception detail text.

## Missing Tests

- No BLOCKER timeout gaps (module `pytestmark` on `test_http_client.py`).
- No explicit case for scheme-relative or unusual URI forms with empty path beyond
  `http://example.test` (low value; same `urlsplit` empty-path path).
- Relative-URL empty path (`""` after urlsplit of odd inputs) not exhaustively matrixed.

## Performance Concerns

None. One additional empty-string check before the existing linear segment scan.

## Follow-up Tasks

| Item | Priority | Status | Notes |
| ---- | -------- | ------ | ----- |
| Optional rename `_assert_no_dot_path_segments` | Low | Not filed | Cosmetic; docs already describe full semantics |
| Percent-encoded dot lookalikes (`%2e`) | Low | Already noted | Remains under PYPOST-1346 tech-debt notes |

### Suite / lint triage (out of scope)

Pre-existing failures outside `test_http_client.py` (e.g. MCP server impl defaults,
dialog LOC discovery drift) are unrelated and remain under their own Jira Debt issues.

No new Jira issues created in Step 7 (instruction: do not create / do not transition).
