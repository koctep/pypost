# PYPOST-1334: Observability Implementation

## Decision

**No production logging or metrics change.** PYPOST-1334 ships example content only
(`examples/collections/github_mcp.json`, `examples/environments/github.json`,
`examples/collections/github_mcp_rest_paths.json`, the `pypost-library.yaml` entry, README
sections, the `check-github-mcp-path-freshness` Makefile target) plus offline tests.
`git diff -- pypost` is empty and production code is out of scope (`10-requirements.md`,
`20-architecture.md`). The 30 `github_*` tools run through PyPost's existing generic MCP and
HTTP pipeline, which already logs, measures and redacts every call. The collection adds no
runtime component, so it needs no event, metric or log field of its own. This mirrors the
GitLab precedent (`ai-tasks/PYPOST-1316/50-observability.md`).

## Existing Observability Covering GitHub Tool Calls

How a `github_*` call runs: `MCPServerImpl.call_tool` (`pypost/core/mcp_server_impl.py`), then
`RequestService` (`pypost/core/request_service.py`), then `HTTPClient.send_request`
(`pypost/core/http_client.py`). Line references below were re-checked against the current tree
and match the PYPOST-1316 analysis.

### Logs (already present, unchanged)

- **ERR**: `http_client.py` — `http_request_timed_out`, `http_connection_failed`,
  `http_request_failed`, `template_integer_conversion_failed` (fires when a `to_int` argument
  such as `pull_number`, `issue_number`, `run_id` or the review comment `line` is not a decimal
  string or integer). URLs pass through `sanitize_text` with env vars. The template error logs
  only the origin.
- **ERR**: `request_service.py` — `retry_loop_invariant_failed`, `request_execution_failed`
  (`request_service.py:384`). `url=%r` is the **template** URL
  (`{{ github_api_url }}/repos/...`). For transport errors the detail is replaced with
  `retries_attempted: N`, so no rendered URL leaks here.
- **WARNING**: `http_client.py` — `response_body_truncated method=… url=… max_bytes=…`
  (`http_client.py:353`; can fire for large `github_list_pull_request_files`,
  `github_list_workflow_runs`, `github_list_pull_requests` or `github_list_issues` responses).
- **WARNING**: `request_service.py` — `retryable_error`, `retryable_status` (only for status codes in the
  configured `retryable_status_codes` policy, for example GitHub `429`/`5xx`), `retry_exhausted`.
  `retryable_error` (`request_service.py:160-169`) and `retry_exhausted`
  (`request_service.py:332`) also log `exc.message`, which for timeouts and connection failures
  embeds the **rendered, unsanitized** URL (`http_client.py:302`, `http_client.py:313`).
- **WARNING**: `mcp_observability.py` — `record_mcp_validation_failure` (wrong type or missing
  argument, for example a non-boolean `draft` or a missing review `event`).
- **INFO**: `mcp_server_impl.py` — `mcp_param_default_applied method=… param=… default_type=…`.
  Fires for the collection's `page`/`per_page` defaults (1/30). Only name and type are logged.
- **DEBUG**: `mcp_server_impl.py` — `mcp_execution_variables_merged` (counts only, via
  `McpSecretsPolicy.safe_execution_log_fields`). `http_client.py` — `request_complete method
  status elapsed_ms size` (no URL, no headers), `sse_stream_detected` (not relevant: GitHub REST
  does not return SSE). `request_service.py` — `retry_policy_resolved`, `retry_backoff`
  (template URL).
- **EMERG / ALERT / CRIT / NOTICE**: N/A. Example content cannot cause system-level failures.

### Metrics (already present, unchanged)

- `track_mcp_request_received(method)`, `track_mcp_response_sent(method, status)`,
  `track_mcp_tool_call_duration(method, outcome, seconds)`,
  `track_mcp_argument_validation_failure(...)`, `track_mcp_param_default_applied(method)` in
  `pypost/core/metrics_registry.py`, recorded through `record_mcp_call_outcome`.
- `track_request_sent(method)`, `track_response_received(method, status_code)` (GitHub
  `401`/`403`/`404`/`422` show up here by status code), `track_response_body_truncated(method)`.
- The MCP activity log (`McpActivityLog`, GUI "MCP activity") records per call the **tool name**
  (`github_list_pull_requests`, ...), outcome, arg count, HTTP status, duration and a detail
  string sanitized by `sanitize_text`.

### Token redaction (confirmed by code reading)

- The GitHub token is sent only as `Authorization: Bearer {{ github_token }}` on all 30
  requests. Tests enforce this (`test_github_mcp_requests_send_github_headers`, mutation twin
  `test_github_mcp_auth_convention_rejects_token_scheme_and_missing_version`). The token never
  appears in a URL or query string.
- `pypost/core/sensitive_text_sanitizer.py`: `_BEARER_TOKEN` turns `Bearer <value>` into
  `Bearer ***` in any text, independent of the token prefix (`ghp_`, `github_pat_`, `gho_`, ...).
  `sanitize_headers` masks the whole `authorization` header value. `_SENSITIVE_JSON_KEY` masks
  JSON keys containing `token` or `authorization`.
- `github_token` is in `hidden_keys` of `examples/environments/github.json` and `secret: true`
  in both the collection variables and the manifest. `_redact_hidden_values` therefore replaces
  its literal value in MCP tool output (`McpResponseSanitizer` for body, logs and error detail),
  and `McpSecretsPolicy` keeps it out of `mcp_overridable_keys` (only `github_owner` and
  `github_repo` are overridable).
- No HTTP log line prints request headers, and `headers_callback` response headers (GitHub
  `X-RateLimit-*`) are not logged. The token reaches no log path in plain text.
- Fixtures hold placeholders only; `test_github_fixtures_contain_no_real_tokens` and its twin
  `test_github_fixtures_secret_scan_rejects_ghp_and_github_pat_values` guard against committed
  real tokens.

### Request URLs with repository identifiers

- Rendered URLs contain `github_api_url`, owner, repository, file paths, `ref`, branch names and
  query values (`state`, `head`, `base`, `labels`). These are repository identifiers and user
  filters, not credentials; the design keeps secrets out of URLs.
- Rendered URLs appear in sanitized ERROR logs, in the unsanitized `response_body_truncated`
  WARNING, and through `exc.message` in `retryable_error` / `retry_exhausted`. This is acceptable
  for GitHub (no secret in the URL) and gives operators the repository that failed. The
  inconsistency itself is generic and already tracked as
  [PYPOST-1333](https://pypost.atlassian.net/browse/PYPOST-1333) (requirements
  `10-requirements.md` scope note).

## Example-Specific Needs

None. The 30 tools are ordinary HTTP requests. Failures (bad token → `401`, missing permission
→ `403`/`404`, invalid review payload → `422`, bad ID → template integer error or argument
validation warning) are already visible through the events and metrics above. The offline
loopback e2e test covers the wire contract; a live GitHub check would be a test or tooling
concern, not observability. No new offline test is added: the precedent added none and the
redaction behaviour is generic, already covered by the sanitizer tests (for example
`tests/test_mcp_response_sanitizer.py`).

## Follow-up Candidates (for Step 7, not implemented)

1. **Low — inconsistent URL sanitization of rendered URLs in logs**: same generic gap as
   PYPOST-1316 (`http_client.py:334`, `http_client.py:353`, `request_service.py:160-169`,
   `request_service.py:332`). Already ticketed as PYPOST-1333; does not affect GitHub because
   no secret is in the URL. No new ticket needed.
2. **Low — no per-tool metric label**: MCP metrics are labelled by HTTP method, so the 30
   GitHub tools collapse into `GET`/`POST`/`PATCH`. Only the in-memory activity log has
   the tool name. Same generic product decision as noted in PYPOST-1316; outside this example
   task.

## Metrics Implementation (if applicable)

N/A: no new metrics. Existing generic metrics cover response time
(`mcp_tool_call_duration_seconds`), throughput (`mcp_requests_received`, `requests_sent`) and
error rate (`mcp_responses_sent{status}`, `responses_received{status_code}`). Business and
system health metrics: N/A, because example data has no runtime component.

## Monitoring Integration

- [ ] Prometheus metrics: N/A (no new metrics; existing ones exported unchanged)
- [ ] Grafana dashboards: N/A
- [ ] Alerting rules: N/A
- [ ] Log aggregation: N/A (no new log events)

## Validation Results

- [x] Logs are correctly formatted: no new logs. Existing `key=value` events reviewed.
- [x] Metrics are collected correctly: no new metrics. The existing MCP/HTTP counters fire for
  GitHub tools through the generic pipeline (exercised by the Step 4 loopback e2e test).
- [x] Logging works in error scenarios: existing ERR/WARNING paths reviewed (timeout,
  connection, integer conversion, validation, retryable status).
- [x] Large data structures are not logged: response bodies are never logged, only size and
  status.
- [x] Token redaction confirmed (Bearer heuristic, header mask, hidden-key value redaction).
- [x] `make lint` and `make verify-ai-tasks`: see the Step 6 sub-items in `00-roadmap.md`.

## Notes

No `pypost/`, `tests/`, `examples/` or `Makefile` change in this step. The only changes are
artifacts under `ai-tasks/PYPOST-1334/`.
