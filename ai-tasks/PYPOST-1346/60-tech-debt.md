# PYPOST-1346: Technical Debt Analysis

## Shortcuts Taken

- **Literal-segment policy only.** The guard rejects path segments that are
  exactly `.` or `..` after render. Percent-encoded lookalikes (`%2e`, `%2E`,
  mixed-case variants) are intentionally out of scope (requirements NFR4 /
  architecture Q&A). With `urlencode` using `quote(..., safe="")`, a literal
  `.` / `..` input stays unencoded; `%2e` only appears if the caller already
  supplied that spelling. This matches LiteLLM-style whole-segment checks and
  deliberately differs from Anthropic SDK’s decode-aware rejection.
- **Empty segments deferred.** `_assert_no_dot_path_segments` skips empty
  strings from `path.split("/")` (leading `/`, `//`). Blank-segment fail-closed
  behaviour remains [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332)
  (To Do); the shared `_prepare_request_kwargs` checkpoint is the intentional
  extension seam.
- **URL-level error, not argument-name-level.** Rejection raises
  `ExecutionError(TEMPLATE)` with a path-segment message after the full URL is
  assembled. Callers do not learn which MCP argument produced the bad segment.
  Accepted in architecture Option B; fixing it would need encode-time or
  per-placeholder context outside this ticket’s DoD.
- **Representative collection coverage only.** GitHub/GitLab offline tests
  cover selected path-bearing tools/args (owner/repo/workflow; project /
  file_path / branch / sha-style). Other tools and collections rely on the
  shared HTTPClient guard without per-tool parametrization (FR5 / DoD-4–5).

## Code Quality Issues

- **Duplicated test assertion helpers.**
  `_assert_dot_path_segment_rejected` is copy-pasted in
  `tests/test_github_mcp_collection.py` and
  `tests/test_gitlab_mcp_collection.py`, with a near-identical method on
  `TestHTTPClientDotPathSegmentRejection`. Low priority; consolidate only if
  more collections add the same pattern.
- **Module-level helper living in `http_client.py`.**
  `_assert_no_dot_path_segments` is a private module function next to
  `HTTPClient`, as designed. When PYPOST-1332 lands, prefer extending this
  helper (or a thin shared path-safety function) rather than a second
  checkpoint elsewhere.
- **No architecture deviation.** Guard placement, TEMPLATE category, unchanged
  `_urlencode`, origin-bounded `dot_path_segment_rejected` ERROR logging, and
  allowlist registration match Step 2 / Step 6.

## Missing Tests

- **No BLOCKER timeout gaps.** Scoped tests inherit module
  `pytestmark = pytest.mark.timeout(...)` (`test_http_client.py` 60s;
  GitHub/GitLab MCP modules 30s).
- **FR4 edge controls are partial.** Green controls cover `ci.yml` (GitHub
  workflow) and a multi-segment GitLab `file_path`. Explicit allow-cases for
  `.github`, `foo.bar`, `..%2Fx`, and `%2e` (must remain allowed under current
  policy) are not automated; behaviour is implied by whole-segment equality.
- **No encode-time / dual-path regression.** Architecture deferred encode-time
  rejection; there is no test asserting `_urlencode(".") == "."` remains true
  while HTTPClient still rejects the assembled path (documented assumption).
- **Other MCP collections.** Bitbucket/Jira/etc. are protected only via the
  shared HTTP stack; no representative offline cases added under this ticket
  (in scope per US4 design, not a DoD gap).

## Performance Concerns

None material. The guard does one `urlsplit` + `path.split("/")` and a linear
segment scan before dispatch. Rejected requests never call `session.request`.
No new metrics series; existing `track_request_error(TEMPLATE)` covers the
RequestService path.

## Follow-up Tasks

### Product / design debt (this change)

| Item | Priority | Status | Notes |
| --- | --- | --- | --- |
| Reject blank rendered path segments at the same HTTP prepare checkpoint | Low | Already ticketed | [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332) — reuse `_assert_no_dot_path_segments` seam / origin-bounded ERROR pattern; do not re-file |
| Optionally reject percent-encoded dot lookalikes (`%2e` / `%2E`) after path assembly (Anthropic-style) if decode-then-normalise proxies become a threat model | Low | Not filed | Explicitly out of PYPOST-1346 scope; document-only. File a Debt issue only if product decides to harden beyond literal segments |
| Optional FR4 allow-case tests (`.github`, `foo.bar`, `..%2Fx`, `%2e`) | Low | Not filed | Nice-to-have regression clarity; not required by DoD |

No new Jira issues created in Step 7 (autonomous instruction: do not create).

### Suite triage (Step 4 `make test`; reconfirmed Step 7)

Verdict for all rows: **NON-BLOCKER — pre-existing** (same failures at task base
commit `38693d0c`). Deduped against open Debt issues; **no new issues created**.

| Test ids | Verdict | Jira |
| --- | --- | --- |
| `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples`<br>`tests/test_makefile_install_seed_contract.py::test_committed_seed_covers_independent_source_inventory` | NON-BLOCKER — pre-existing | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) (To Do) |
| `tests/test_pypost_1077_verification_votes.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`<br>`tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | NON-BLOCKER — pre-existing | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) (To Do) |
| `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift` | NON-BLOCKER — pre-existing | [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) (To Do) |

Scoped PYPOST-1346 tests (HTTPClient dot-segment class, GitHub/GitLab prepare
reject + legitimate controls, assertLogs observability) are green and are not
part of the pre-existing set.
