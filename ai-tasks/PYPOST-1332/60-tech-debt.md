# PYPOST-1332: Technical Debt Analysis

## Shortcuts Taken

- **Always-on blank rejection (not opt-in).** Jira description mentioned an optional
  manifest/environment `required` flag. Product acceptance and architecture chose
  always-on fail-closed at the shared HTTP prepare seam (parity with PYPOST-1346). A
  per-variable required UX layer was not built.
- **Helper name retained.** `_assert_no_dot_path_segments` now also rejects blanks; rename
  to `_assert_safe_path_segments` deferred to avoid a wide doc/test churn for no behaviour
  change. Docs call out the extended semantics.
- **URL-level error, not argument-name-level.** Same as PYPOST-1346 Option B: callers see
  TEMPLATE path-segment wording, not which MCP arg was blank.
- **Whitespace-only segments.** Only empty `""` pieces after `path.split("/")` are
  rejected. A literal space segment is still a non-empty segment (and would typically be
  percent-encoded if passed through `urlencode`).
- **Representative collection coverage only.** GitLab blank `gitlab_project` on get-project
  / get-file; GitHub blank owner/repo on get-repository. Other tools rely on the shared
  guard.

## Code Quality Issues

- **Duplicated blank assertion helpers** in GitHub/GitLab MCP test modules (mirrors the
  existing duplicated `_assert_dot_path_segment_rejected`). Low priority.
- **Event dispatch via detail string prefix** (`Blank path segment`) couples log event
  naming to exception detail text. Acceptable for two closely related rejects; a small
  reason enum would be cleaner if a third reject class appears.
- **No architecture deviation.** Same checkpoint, TEMPLATE category, origin-bounded ERROR
  logging, allowlist registration.

## Missing Tests

- No BLOCKER timeout gaps (module `pytestmark` inherited).
- No explicit Jira-collection blank `jira_project_key` offline case (shared HTTP guard;
  called out in ticket text as a beneficiary, not a DoD item).
- No encode-time dual-path regression asserting `_urlencode("") == ""` while prepare still
  rejects (documented assumption).

## Performance Concerns

None material. One `urlsplit` + linear segment scan (already present for dots). Rejected
requests never call `session.request`.

## Follow-up Tasks

### Product / design debt (this change)

| Item | Priority | Status | Notes |
| --- | --- | --- | --- |
| Optional rename `_assert_no_dot_path_segments` → `_assert_safe_path_segments` | Low | Not filed | Docs already describe blank+dot behaviour; rename is cosmetic |
| Optional per-variable `required` flag at MCP/manifest layer | Low | Not filed | Explicitly out of DoD; always-on path guard is the product contract |
| Optional Jira collection blank `jira_project_key` offline prepare | Low | Not filed | Covered by shared HTTPClient guard |
| Percent-encoded dot lookalikes (`%2e`) | Low | Already noted | Remains under PYPOST-1346 tech-debt notes; do not re-file |

No new Jira issues created in Step 7 (autonomous instruction: do not create).

### Suite / lint triage

| Item | Verdict | Notes |
| --- | --- | --- |
| `tests/test_mcp_server_registry.py:308` E501 (`make lint` / lint-tests baseline) | NON-BLOCKER — pre-existing | Unrelated to PYPOST-1332; present before this change |
| Scoped blank/dot HTTPClient + GitHub/GitLab prepares | Green | Not part of pre-existing failure set |

Pre-existing full-suite failures (if any) from earlier tickets (e.g. packaging /
lockfile / discovery votes) are unchanged by this work; none were re-filed.
