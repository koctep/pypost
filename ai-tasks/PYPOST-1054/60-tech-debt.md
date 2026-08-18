# PYPOST-1054: Technical Debt Analysis

**Verdict:** Delivery matches `20-architecture.md`. Optional `maxResults`/`startAt`
now default safely (50/0) at the MCP execution boundary, are published in the
JSON Schema `default` property, and the UI table round-trips them. No new
crutches in production code; the two shortcuts below are pre-existing design
choices this task extends rather than something new it introduced. **SAFE TO
CLOSE** for Step 7 — no merge blockers. 144 targeted tests green (Steps 4-6 re-run
confirmed above); 4 unrelated pre-existing failures found elsewhere in the full
suite, documented below as NON-BLOCKER.

Scope reviewed: `pypost/models/models.py` (`McpToolParam.default`),
`pypost/core/mcp_tool_contract.py` (schema `default` publication),
`pypost/core/mcp_server_impl.py` (`_build_execution_variables` defaulting, new
log line, new counter), `pypost/ui/widgets/request_editor.py`
(`McpParamsTable` default preservation), `examples/collections/jira_mcp.json`
(`jira-list-boards`, `jira-list-board-sprints`, `jira-get-sprint-issues`),
`pypost/core/metrics_protocol.py`, `pypost/core/metrics_registry.py`,
`pypost/core/metrics_otel.py`, `pypost/core/qt/metrics.py`,
`scripts/audit_baseline_metrics.py`, `ai-tasks/PYPOST-376/baseline-metrics.md`,
and all touched test files. `ai-tasks/PYPOST-1054/{10..50}-*.md` and
`ai-tasks/PYPOST-1029/60-tech-debt.md` (origin story) read for context.

---

## Shortcuts Taken

- **`default` is not type-checked against `type` (Priority: Medium).**
  `McpToolParam.model_post_init` (`pypost/models/models.py:23-25`) validates
  that `type` is one of `_MCP_PARAM_TYPES` but never validates that `default`'s
  Python type is consistent with the declared `type` (e.g. a param declared
  `type="boolean"` with `default="fifty"` constructs without error). The
  mismatch would only surface later, either in the JSON Schema an agent
  receives or when a Jinja/`to_int`-style conversion fails at execution time.
  `Optional[Any]` was the pragmatic choice to support every declared type
  without a discriminated union; a `model_validator` cross-checking `default`
  against `type` at construction time would close this without changing the
  public field.
- **No UI affordance to author a `default` (Priority: Medium).** Per
  `20-architecture.md` item 4, `McpParamsTable` was scoped to *preserve*
  `McpToolParam.default` across `set_data()`/`get_data()` round-trips, not to
  let a user view or edit it — there is no fifth "Default" column or dialog.
  Two consequences: (1) a user cannot give a brand-new optional param a
  default from the GUI at all (only fixture/JSON authors can); (2) renaming a
  param's "Name" cell in the table silently drops any preserved default,
  because `get_data()` looks it up by the (now-changed) key via
  `self._defaults.get(name)` (`pypost/ui/widgets/request_editor.py:552`) with
  no rename tracking. Neither is a regression — this mirrors the architecture's
  explicit "preserve, don't edit" scope — but it is a real ergonomics gap for
  UI-driven collection editing that a future task should close with a proper
  editable column.
- **`default=None` cannot express "the true default is null" (Priority:
  Low).** `None` doubles as both "no default declared" and would-be "default
  value is null" — there is no way today to distinguish the two. No current
  curated tool needs a null default, so this is a latent limitation, not an
  active bug.
- **Only 3 of the fixture's list-shaped tools got the pattern (Priority:
  Low, scope note — see explicit check below).** `jira-search-assignable-users`
  is also a list/search-shaped GET request (against
  `/rest/api/3/user/assignable/search`, which the live Jira REST API paginates
  with `maxResults`/`startAt`) but the curated fixture never exposed those
  query params for it at all — not "left required," genuinely absent. Adding
  them is a bigger change (new params + template wiring), not just flipping
  `required`/`default`, so it was correctly out of this task's DoD (which
  scoped exactly the three tools carried over from PYPOST-1029). Recorded as
  TD-3 below for a future ticket.

---

## Code Quality Issues

- **`mcp_arg_count` semantic shift in the pre-existing DEBUG log line
  (Priority: Low, non-blocking — flagged by the Step 6 reviewer).**
  `_build_execution_variables` (`pypost/core/mcp_server_impl.py`) used to
  compute `counts = McpSecretsPolicy.safe_execution_log_fields(..., len(mcp_args))`
  from the raw caller-supplied `mcp_args`. It now computes
  `len(merged_args)` — `merged_args` is `mcp_args` plus whatever pagination
  defaults were injected — so the pre-existing `mcp_execution_variables_merged`
  DEBUG line's `mcp_arg_count` field silently changed meaning from "how many
  args did the caller actually pass" to "how many args are present after
  defaulting." The new `defaults_applied_count` field lets a reader recover
  the old number (`mcp_arg_count - defaults_applied_count`), so no information
  is lost, but the field's own semantics moved without a doc update anywhere
  and no test pins the old behavior. Not a Completion Criteria violation
  (nothing asserts the prior meaning), but worth a one-line clarification in
  `50-observability.md` or the log call's own comment in a follow-up.
- **`pypost/core/mcp_server_impl.py` is close to its SOLID-audit growth
  budget (Priority: Low).** This task grew the file 282 -> 303 lines against
  a 325-line cap (22 lines of headroom left; no re-derivation needed now).
  Flagging so the next feature that touches this file budgets for a possible
  cap re-derivation in `scripts/audit_baseline_metrics.py`.
- **`pypost/core/qt/metrics.py` has very little headroom left (Priority:
  Low).** Cap was just re-derived 181 -> 185 for the new
  `track_mcp_param_default_applied` delegation (182 measured); only 3 lines
  of headroom remain before the next metric addition needs another
  re-derivation. Purely a bookkeeping note for whoever adds the next counter.
- **Pagination descriptions are repetitive across the three fixture entries
  (Priority: Low, carried over from PYPOST-1029, unchanged by this task).**
  "Defaults to 50 when omitted" / "Defaults to 0 when omitted" is duplicated
  verbatim across `jira-list-boards`, `jira-list-board-sprints`, and
  `jira-get-sprint-issues`. Still acceptable for fixture clarity (each is
  agent-facing text, not shared code), but a shared description template
  would reduce drift risk if a 4th list tool is ever added (see TD-3).

---

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Schema publishes `default` and omits optional param from `required` | Present (`test_schema_includes_default_and_omits_optional_from_required`) |
| Runtime defaults injected when args omitted (`maxResults`/`startAt`) | Present (`test_call_tool_applies_mcp_param_defaults_when_args_omitted`) |
| Explicit custom pagination args override defaults | Present (`test_call_tool_honors_explicit_custom_pagination_args`) |
| INFO log + counter fire once per defaulted param | Present (`test_call_tool_applying_defaults_tracks_metric_and_logs`) |
| Explicit args stay silent (no log/metric, `defaults_applied_count=0`) | Present (`test_call_tool_explicit_args_skip_default_metric_and_logs`) |
| UI table round-trips `default` unchanged (no rename) | Present (`test_round_trip_preserves_default`) |
| Curated Jira list fixtures expose optional + default pagination params | Present (`test_jira_mcp_list_requests_expose_pagination_mcp_params`) |
| Counter/log wiring across all 4 `MetricsTrackerProtocol` implementers | Present (`test_metrics_registry.py`, `test_metrics_otel.py`, `test_metrics_manager.py`, `test_metrics_protocol.py`) |
| Defaulting for a *non*-pagination-shaped optional param (e.g. `string`/`boolean` type) | Missing — only the two `integer_or_string` pagination params are exercised end-to-end, though `_build_execution_variables`'s new loop is fully generic over any `mcp_params` entry with a declared default |
| UI: renaming a param key that carries a default (drops the default, see Shortcuts) | Missing |
| `McpToolParam` construction with `default`'s type mismatching declared `type` | Missing — would currently pass silently (see Shortcuts / Code Quality) |
| `jira-search-assignable-users` pagination | Missing by design — params were never added (TD-3) |

**Timeout marker review: NO BLOCKER.** All touched/added tests live in modules
that already declare module-level `pytestmark = pytest.mark.timeout(...)`
(`tests/test_mcp_server_impl.py` — 60s, restored by Step 5 after a Step 4
regression; `tests/test_mcp_tool_contract.py`, `tests/test_example_fixtures.py`,
`tests/test_request_editor_mcp_params.py`, `tests/test_metrics_registry.py`,
`tests/test_metrics_otel.py`, `tests/test_metrics_manager.py`,
`tests/test_metrics_protocol.py`, `tests/test_solid_audit_baseline.py` — all
verified present). Re-ran all 9 modules together: 144 passed.

---

## Performance Concerns

None. Default injection is a synchronous in-memory dict/loop over at most a
handful of `mcp_params` entries per call, already inside the span covered by
the existing `mcp_tool_call_duration_seconds` histogram — no new I/O, no new
hot-path allocation of consequence. Matches `50-observability.md`'s own
assessment; re-confirmed by inspection, nothing new found.

---

## Deviations from Architecture

None material. `20-architecture.md`'s module interfaces
(`McpToolParam.default`, `build_tool_input_schema`'s `prop["default"]`,
`_build_execution_variables(..., request_data=None)`, `McpParamsTable`
preservation, the three fixture updates) all match what shipped. The one
Q&A-anticipated behavior ("what happens if a caller passes `None`") is
implemented exactly as specified (`merged_args[param_name] is None` also
triggers defaulting).

---

## Follow-up Tasks

### TD-1 — Low (non-blocking, recorded per Step 6 reviewer note)

- **Item:** Document (or revert) the `mcp_arg_count` DEBUG-log semantic shift
  in `_build_execution_variables` — the field now counts post-merge/post-default
  args instead of the raw caller-supplied count.
- **Notes:** No test pins the old semantics and no Completion Criteria is
  violated; the new `defaults_applied_count` field lets a log reader recover
  the prior number by subtraction. Fix is a one-line doc/comment clarification,
  or splitting the field into `mcp_arg_count_raw` / `mcp_arg_count_merged` if a
  future consumer needs both without doing arithmetic.
- **Jira:** [PYPOST-1090](https://pypost.atlassian.net/browse/PYPOST-1090)

### TD-2 — Medium

- **Item:** Add a `model_validator` on `McpToolParam` that checks `default`'s
  Python type is consistent with the declared `type` field (e.g. reject
  `default="x"` when `type="boolean"`), and add an editable "Default" column
  (or edit dialog) to `McpParamsTable` in `pypost/ui/widgets/request_editor.py`
  so defaults can be authored from the UI, not just preserved from JSON, and
  survive a param rename.
- **Notes:** Two related UX/safety gaps from this task's scope boundary
  ("preserve, don't validate or edit"); bundling them is reasonable since both
  touch the same `McpToolParam`/`McpParamsTable` surface, but could be split
  into two tickets (model validation vs. UI editing) if sizing prefers that.
- **Jira:** [PYPOST-1089](https://pypost.atlassian.net/browse/PYPOST-1089)

### TD-3 — Low

- **Item:** Evaluate exposing `maxResults`/`startAt` (with the same
  optional-with-safe-default pattern this task established) on
  `jira-search-assignable-users`, and consider whether `jira-search-issues-jql`'s
  raw `search_payload` JSON body should get equivalent pagination guidance in
  its `mcp_description` (it cannot get a structural `default` since the body is
  an opaque string, not discrete `mcp_params`).
- **Notes:** Explicit answer to this task's own "any other curated list tools
  left out of scope" question — confirmed via full param dump of
  `examples/collections/jira_mcp.json`: no other tool already declares
  `maxResults`/`startAt` as `required: true`; these two are the only
  list/search-shaped tools without pagination params at all.
- **Jira:** [PYPOST-1091](https://pypost.atlassian.net/browse/PYPOST-1091)

### NON-BLOCKER — pre-existing (found during Step 7's full-suite spot-check; already
flagged by Steps 5/6 as pre-existing and out of scope, re-confirmed here with
exact node ids and current failure text)

- **Node IDs:**
  - `tests/test_mcp_server_manager.py::test_format_mcp_bind_error_addr_in_use`
  - `tests/test_metrics_server_startup.py::TestFormatBindError::test_metrics_addr_in_use_message`
  - `tests/test_encryption_migrate_cli.py::test_cli_re_encrypt_dry_run`
  - `tests/test_encryption_migration.py::test_bulk_re_encrypt_dry_run_projects_active_kid`
- **Details:** The first two hardcode `exc.errno = 48` (macOS/BSD `EADDRINUSE`)
  instead of `errno.EADDRINUSE`; on this Linux sandbox
  (`errno.EADDRINUSE == 98`) the "busy" formatting branch in
  `pypost/core/server_bind.py` never triggers, so the assertion
  `"busy" in message.lower()` fails against the real message `"...Address
  already in use"`. The other two are order/randomness-dependent: re-running
  `test_cli_re_encrypt_dry_run` and
  `test_bulk_re_encrypt_dry_run_projects_active_kid` together during this
  Step 7 spot-check flipped which one failed between two consecutive runs
  (`kid_histogram` compares a freshly-generated key id against a stale
  expected literal) — consistent with Step 5's documented finding of
  unstable membership across repeated runs. None of the 4 files or the
  production code they exercise (`pypost/core/server_bind.py`,
  `pypost/core/qt/mcp_server.py`, `pypost/core/qt/metrics.py`,
  `pypost/core/encryption_migration.py`) were touched by PYPOST-1054.
- **Repro:** `pytest -q tests/test_encryption_migrate_cli.py
  tests/test_encryption_migration.py tests/test_mcp_server_manager.py
  tests/test_metrics_server_startup.py`
- **Jira search performed:** `jira_search_issues_jql` for `EADDRINUSE`,
  `errno`, `addr_in_use`, `kid_histogram`, `re_encrypt`, `encryption_migration`
  returned no existing issue covering either root cause.
- **Jira:** [PYPOST-1088](https://pypost.atlassian.net/browse/PYPOST-1088)

---

## Blocker Review

| Check | Requirement | Status | Notes |
| ----- | ----------- | ------ | ----- |
| Pytest Timeouts | Explicit timeout marker on all touched tests | PASS | Verified present on all 9 re-run modules |
| Test Suite | All touched and contract tests pass cleanly | PASS | 144/144 re-run in this step |
| Static Analysis | Zero linter errors on touched files | PASS | Per Steps 5-6; unchanged since |
| Architecture & DoD | Matches approved architecture | PASS | See Deviations section above |
| Pre-existing failures | Filed or explicitly out of scope | NON-BLOCKER | 4 node ids documented above, none caused by this task, none previously ticketed |
| **Verdict** | Release / merge gate readiness | **SAFE TO CLOSE** | No blockers; proceed to Step 8 |
