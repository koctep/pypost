# PYPOST-1316: Observability Implementation

## Decision

**No production logging or metrics change.** PYPOST-1316 ships example content only
(`examples/collections/gitlab_mcp.json`, `examples/environments/gitlab.json`,
`examples/collections/gitlab_mcp_rest_paths.json`, the `pypost-library.yaml` entry, a README
section, the `check-gitlab-mcp-path-freshness` Makefile target) plus tests.
`git diff -- pypost` is empty and production code is out of scope (`10-requirements.md`,
`20-architecture.md`). The GitLab tools run through PyPost's existing generic MCP and HTTP
pipeline. That pipeline already logs, measures and redacts every call to them. Nothing in the
collection is a new runtime component, so it needs no event, metric or log field of its own.

## Existing Observability Covering GitLab Tool Calls

How a `gitlab_*` call runs: `MCPServerImpl.call_tool` (`pypost/core/mcp_server_impl.py`), then
`RequestService` (`pypost/core/request_service.py`), then `HTTPClient.send_request`
(`pypost/core/http_client.py`).

### Logs (already present, unchanged)

- **ERR**: `http_client.py` — `http_request_timed_out`, `http_connection_failed`,
  `http_request_failed`, `template_integer_conversion_failed` (fires when a `to_int` GitLab ID
  argument such as `issue_iid` or `merge_request_iid` is not a decimal string or integer). URLs
  pass through `sanitize_text` with env vars. The template error logs only the origin.
- **ERR**: `request_service.py` — `retry_loop_invariant_failed` (template URL, not rendered).
- **WARNING**: `http_client.py` — `response_body_truncated method=… url=… max_bytes=…` (can fire
  for large `gitlab_get_file` / list responses).
- **WARNING**: `request_service.py` — `retryable_error`, `retryable_status` (for example GitLab
  `429`/`5xx`), `retry_exhausted`. The `url=%r` field is the **template** URL
  (`{{ gitlab_base_url }}/api/v4/...`). But `retryable_error` (`request_service.py:160-169`) and
  `retry_exhausted` (`request_service.py:332-342`) also log `error=%s` from `exc.message`. For a
  timeout or connection failure that text is `f"Request to {url} timed out."` /
  `f"Could not connect to {url}."` (`http_client.py:302`, `http_client.py:313`), so the
  **rendered, unsanitized** URL can appear.
- **ERR**: `request_service.py` — `request_execution_failed` (`request_service.py:384-390`) logs
  the template URL in `url=%r` and `detail=%s` from `exc.detail`. Transport errors (timeout,
  connection, generic request, template) leave the retry loop only on the last attempt, which
  replaces the detail with `retries_attempted: N` (`request_service.py:157`, also for
  `max_retries=0`). The other errors that reach it (BODY, YAML parse, CANCELLED) carry no URL.
  So this event does not leak the rendered URL.
- **WARNING**: `mcp_observability.py` — `record_mcp_validation_failure` (wrong argument type or
  missing argument for a GitLab tool).
- **INFO**: `mcp_server_impl.py` — `mcp_param_default_applied method=… param=… default_type=…`.
  Fires for the collection's `page`/`per_page` defaults (1/20). Only the name and type are
  logged, never the value.
- **DEBUG**: `mcp_server_impl.py` — `mcp_execution_variables_merged` (counts only, via
  `McpSecretsPolicy.safe_execution_log_fields`). `http_client.py` — `request_complete
  method status elapsed_ms size` (no URL), `sse_stream_detected` (not relevant: GitLab REST does
  not return SSE). `request_service.py` — `retry_policy_resolved`, `retry_backoff` (template URL).
- **EMERG / ALERT / CRIT / NOTICE**: N/A. Example content cannot cause system-level failures.

### Metrics (already present, unchanged)

- `track_mcp_request_received(method)`, `track_mcp_response_sent(method, status)`,
  `track_mcp_tool_call_duration(method, outcome, seconds)`,
  `track_mcp_argument_validation_failure(...)`, `track_mcp_param_default_applied(method)` in
  `pypost/core/metrics_registry.py`, recorded through `record_mcp_call_outcome`.
- `track_request_sent(method)`, `track_response_received(method, status_code)` (GitLab
  `401`/`403`/`404` show up here by status code), `track_response_body_truncated(method)`.
- The MCP activity log (`McpActivityLog`, GUI "MCP activity") records per call: **tool name**
  (`gitlab_list_issues`, ...), outcome, arg count, HTTP status, duration and a detail string.
  The detail is sanitized by `sanitize_text`.

### Token redaction (confirmed)

- The GitLab token is sent only as `Authorization: Bearer {{ gitlab_token }}`. A test enforces
  this convention (`test_gitlab_mcp_requests_use_bearer_auth_convention`, plus a mutation twin
  that rejects `PRIVATE-TOKEN`). The token never appears in a URL or query string.
- `pypost/core/sensitive_text_sanitizer.py`: `_BEARER_TOKEN` turns `Bearer <value>` into
  `Bearer ***` in any text. `sanitize_headers` masks the whole `authorization` header value.
  `_SENSITIVE_JSON_KEY` masks JSON keys that contain `token` or `authorization`.
- `gitlab_token` is declared hidden in `examples/environments/gitlab.json` and `secret` in the
  manifest. As a result, `_redact_hidden_values` replaces its literal value in MCP tool output
  (`format_structured_tool_result`, `McpResponseSanitizer` for body, logs and error_detail).
  `McpSecretsPolicy` also blocks MCP callers from overriding it.
- No HTTP log line prints request headers. The token therefore reaches no log path in plain
  text.

### Request URLs with project paths

- Rendered GitLab URLs contain `gitlab_base_url`, the URL-encoded project path, file paths,
  `ref`, and `search`/`state`/`labels` query values. These are repository identifiers and user
  search terms, not credentials. The design keeps secrets out of URLs (token in header only).
- Rendered URLs appear in sanitized ERROR logs and in the unsanitized
  `response_body_truncated` WARNING. Retry and request-failure logs put the template URL in
  `url=%r`, but the rendered, unsanitized URL can still appear through `exc.message`
  (`retryable_error`, `retry_exhausted`). `request_execution_failed` logs only
  `retries_attempted: N` as detail for transport errors, so it carries no rendered URL. Logging
  project paths at these levels is acceptable for GitLab: the token travels only in the
  `Authorization` header and the URLs contain no secrets by design. It matches how every other collection (for example
  Jira, which has issue keys and JQL in the URL) is handled, and it is what an operator needs
  to see which repository failed.

## Example-Specific Needs

None. The 25 tools are ordinary HTTP requests. Failures (bad token → `401`, wrong project →
`404`, bad ID → template integer error or argument validation warning) are already visible
through the events and metrics above. Offline tests (loopback e2e) cover the wire contract. A
live GitLab check would be a test or tooling concern, not observability.

## Follow-up Candidates (for Step 7, not implemented)

1. **Low — inconsistent URL sanitization of rendered URLs in logs**: in `http_client.py`,
   `response_body_truncated` (WARNING, `http_client.py:354`) and `sse_stream_detected` (DEBUG,
   `http_client.py:335`) log the rendered `url` without `sanitize_text`. In
   `request_service.py`, `retryable_error` (WARNING, `request_service.py:160-169`) and
   `retry_exhausted` (WARNING, `request_service.py:332-342`) log `exc.message`, which embeds
   the rendered URL for timeouts and connection failures (`http_client.py:302`,
   `http_client.py:313`). The
   `http_client.py` ERROR events do sanitize the URL. This does not affect GitLab (no secret in
   the URL). It matters for collections that put a hidden value in the path or in an unlisted
   query key. It is generic and predates this task.
2. **Low — no per-tool metric label**: MCP metrics are labelled by HTTP method, so the 25
   GitLab tools collapse into `GET`/`POST`/`PUT` in Prometheus. Only the in-memory activity log
   has the tool name. Adding a bounded `tool` label is a generic product decision, outside this
   example task.

## Metrics Implementation (if applicable)

N/A: no new metrics. The existing generic metrics listed above cover response time
(`mcp_tool_call_duration_seconds`), throughput (`mcp_requests_received`, `requests_sent`) and
error rate (`mcp_responses_sent{status}`, `responses_received{status_code}`). Business metrics and
system health metrics: N/A, because example data has no runtime component.

## Monitoring Integration

- [ ] Prometheus metrics: N/A (no new metrics; existing ones exported unchanged)
- [ ] Grafana dashboards: N/A
- [ ] Alerting rules: N/A
- [ ] Log aggregation: N/A (no new log events)

## Validation Results

- [x] Logs are correctly formatted: no new logs. Existing `key=value` events reviewed.
- [x] Metrics are collected correctly: no new metrics. The existing MCP/HTTP counters fire for
  GitLab tools through the generic pipeline (exercised by the loopback e2e test from Step 4).
- [x] Logging works in error scenarios: existing ERR/WARNING paths reviewed (timeout,
  connection, integer conversion, validation, retryable status).
- [x] Large data structures are not logged: response bodies are never logged. Only size and
  status are.
- [x] Token redaction confirmed (Bearer heuristic + header mask + hidden-key value redaction).
- [x] `make verify-ai-tasks`: see the Step 6 sub-items in `00-roadmap.md`.

## Notes

No `pypost/`, `tests/`, `examples/` or `Makefile` change in this step. The only change is to
artifacts under `ai-tasks/PYPOST-1316/`.
