# Logging Event Naming Convention (PYPOST-747)

## Overview

PyPost uses Python stdlib `logging` with a **key=value event convention** in newer modules. Log
lines are plain text (not JSON), but the message body follows a predictable structure so
operators, tests, and CI guardrails can grep and classify events reliably.

This document is the canonical reference for naming new events and migrating legacy messages.
It complements [observability_audit.md](observability_audit.md) (audit inventory and gaps),
[security_audit.md](security_audit.md) (sensitive fields), and [testing.md](testing.md) (pytest
`log_cli` and CI allowlists).

**Do not use `print()` in `pypost/`** — `make lint` runs flake8 with the `flake8-print` plugin
(T201) on application code. Use `logging.getLogger(__name__)` instead (PYPOST-752).

## Log Format

Root configuration is applied at startup in `pypost/main.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
```

After settings load, the root level is updated from `settings.log_level` (`log_level_applied`
event). Logger names follow the module path (for example `pypost.core.http_client`).

### Preferred message shape

```text
<event_name> <key1>=<value1> <key2>=<value2> ...
```

Rules:

| Rule | Example |
| --- | --- |
| Event name is **snake_case**, first token, no spaces | `mcp_activity_recorded` |
| Context fields are **space-separated `key=value`** pairs | `operation=call_tool outcome=success` |
| Use **`%` formatting**, not f-strings | `logger.info("request_sent method=%s url=%s", method, url)` |
| Values with spaces or special chars use **`%r`** or quoting in docs | `endpoint=%r` |
| Booleans as lowercase strings | `webhook=true`, `opened_blank_tab=true` |
| Outcome suffixes: `_started`, `_completed`, `_failed`, `_cancelled` | `save_as_flow_started` |
| Injection / composition: `_source source=injected\|new` | `storage_source source=injected` |

Example (INFO):

```text
2026-07-14 12:00:00 pypost.core.mcp_activity_log INFO mcp_activity_recorded operation=call_tool outcome=success tool_name=foo tool_count=1 mcp_arg_count=2 http_status=200 duration_ms=45
```

### Exceptions

| Sink | Format | Notes |
| --- | --- | --- |
| Alert rotating file | JSON lines via dedicated logger | `AlertManager` file logger only |
| Legacy modules | Human-readable prefix | See [Legacy migration](#legacy-migration) |
| Uvicorn (metrics/MCP threads) | Uvicorn default | Suppressed to WARNING on server threads |

## Domain Event Catalog

Inventory date: 2026-07-14 (~330 `logger.*` calls across 47 modules). Events are grouped by
functional domain. **Level** is the typical level; some events log at multiple levels in
different call sites.

### Application lifecycle

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `app_startup` | INFO | — | `main` |
| `app_shutdown` | INFO | — | `main` |
| `log_level_applied` | INFO | `level` | `main` |
| `template_service_created` | INFO | `id` | `main` |
| `storage_created` | INFO | `id`, `encryption_applied` | `main` |
| `request_manager_created` | INFO | `id` | `main` |
| `history_manager_created` | INFO | `id` | `main` |
| `mcp_manager_created` | INFO | `id` | `main` |
| `alert_manager_created` | INFO | `log_path`, `webhook_url_set` | `main` |
| `main_window_initialized` | INFO | — | `ui/main_window` |
| `main_window_ui_ready` | INFO | — | `ui/main_window` |
| `main_window_exit_requested` | INFO | — | `ui/main_window` |
| `main_window_exit_storage_idle` | INFO | `completed` | `ui/main_window` |
| `settings_applied` | INFO | `font_size`, `indent_size`, `request_timeout` | `ui/main_window` |
| `agent_session_started` | INFO | `offscreen`, `ready_timeout_s`, `metrics_port`, `config_dir`, `data_dir` | `agent/lifecycle` |
| `agent_session_ready` | INFO | `ready_ms`, `launch_ms`, `metrics_port` | `agent/lifecycle` |
| `agent_session_ready_timeout` | WARNING | `ready_timeout_s`, `waited_ms`, `metrics_port` | `agent/lifecycle` |
| `agent_session_shutdown_started` | INFO | `metrics_port`, `started` | `agent/lifecycle` |
| `agent_session_shutdown_completed` | INFO | `shutdown_ms`, `metrics_port` | `agent/lifecycle` |
| `agent_session_mcp_stop_failed` | ERROR | exception | `agent/lifecycle` |
| `agent_session_handle_exit_failed` | ERROR | exception | `agent/lifecycle` |
| `agent_session_window_close_failed` | ERROR | exception | `agent/lifecycle` |
| `agent_session_metrics_stop_failed` | ERROR | exception | `agent/lifecycle` |
| `agent_session_temp_cleanup_failed` | ERROR | exception | `agent/lifecycle` |
| `agent_session_failure_dump_hook_failed` | WARNING | `error` | `agent/lifecycle` |
| `ui_snapshot_captured` | DEBUG | `node_count`, `named_count`, `duration_ms` | `agent/ui_snapshot` |
| `ui_action_applied` | DEBUG | `primitive`, `widget_id`, `outcome`, `duration_ms` | `agent/ui_actions` |
| `ui_wait_settled` | DEBUG | `condition`, `waited_ms`, `timeout_s` | `agent/ui_wait` |
| `ui_wait_timeout` | DEBUG | `condition`, `waited_ms`, `timeout_s` | `agent/ui_wait` |
| `agent_e2e_seed_completed` | INFO | `data_dir`, ids, counts | `fixtures/agent_e2e_seed` |
| `agent_e2e_seed_failed` | ERROR | `data_dir`, exception | `fixtures/agent_e2e_seed` |
| `agent_e2e_fixture_ready` | INFO | `mode=blank\|seeded` | `_pytest_plugins/agent_e2e` |
| `agent_e2e_http_stub_installed` | INFO | `name` (catalog, `url_router`, or custom) | `fixtures/agent_e2e_http` |
| `agent_e2e_failure_artifacts_written` | INFO | `path`, `nodeid` | `fixtures/agent_e2e_failure` |
| `agent_e2e_failure_artifacts_failed` | WARNING | `nodeid`, `error` | `fixtures/agent_e2e_failure` |
| `*_source` | DEBUG | `source=injected\|new` | composition-root injectors |

Agent session contract and ready-gate semantics:
[agent_lifecycle.md](agent_lifecycle.md). Packaging fixtures emit
`agent_e2e_fixture_ready` after ready ([agent_e2e.md](agent_e2e.md));
caplog proof for blank/seeded modes lives in
`tests/test_agent_e2e_packaging_logs.py` (PYPOST-867). HTTP stubs emit
`agent_e2e_http_stub_installed`
([agent_e2e_http.md](agent_e2e_http.md)); caplog proof for the install
event lives in `tests/test_agent_e2e_http_stub_logs.py` (PYPOST-870);
failure dumps emit
`agent_e2e_failure_artifacts_written` /
`agent_e2e_failure_artifacts_failed`
([agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md)); compose
with `agent_session_*` / `agent_e2e_seed_*`. Snapshot capture contract:
[ui_snapshot.md](ui_snapshot.md) (`ui_snapshot_captured` logs scalars only —
never the tree or values). UI action contract:
[ui_actions.md](ui_actions.md) (`ui_action_applied` logs scalars only — never
fill text, option labels, or key payloads). Settle waits:
[ui_wait.md](ui_wait.md) (`ui_wait_settled` / `ui_wait_timeout` — timing
scalars only; diagnostics live on `UiWaitTimeoutError`).

### Configuration and settings

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `config_directory_create_failed` | ERROR | `path`, `error` | `config_manager` |
| `config_load_failed` | ERROR | `path`, `error` | `config_manager` |
| `config_save_failed` | ERROR | `path`, `error` | `config_manager` |
| `bind_address_settings_validation_failed` | WARNING | `field`, `reason` | settings UI |
| `retryable_codes_settings_validation_failed` | WARNING | `reason` | settings UI |
| `settings_encryption_verify_started` | INFO | — | encryption settings |
| `settings_encryption_*_started` | INFO | operation name | encryption settings |
| `settings_encryption_*_completed` | INFO | operation, counts | encryption settings |
| `settings_encryption_*_cancelled` | INFO | operation | encryption settings |
| `settings_encryption_migration_worker_failed` | ERROR | `error` | encryption settings |

### HTTP requests and retries

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `request_send_initiated` | INFO | `method`, `url`, `request_id` | `tabs_presenter` |
| `request_stop_requested` | INFO | `method`, `url` | `tabs_presenter` |
| `request_finished` | INFO | `method`, `status_code`, `elapsed_time`, `size` | worker |
| `request_cancelled` | INFO | `category` or `error_msg` | worker |
| `request_error` | ERROR | `category`, `message`, `detail` | worker |
| `request_execution_failed` | ERROR | `method`, `url`, `category`, `detail` | `request_service` |
| `http_attempt` | DEBUG | `method`, `url`, `attempt`, `max_retries` | `request_service` |
| `retry_policy_resolved` | DEBUG | `method`, `url`, `source`, `max_retries` | `request_service` |
| `retry_backoff` | DEBUG | `method`, `url`, `attempt`, `wait_seconds` | `request_service` |
| `retry_cancelled_during_backoff` | DEBUG | `method`, `url`, `attempt` | `request_service` |
| `retryable_status` | WARNING | `method`, `url`, `status`, `attempt`, `max_retries` | `request_service` |
| `retryable_error` | WARNING | `method`, `url`, `category`, `attempt`, `max_retries` | `request_service` |
| `retry_exhausted` | WARNING | `method`, `url`, `request_name`, `retries` | `request_service` |
| `retry_loop_invariant_failed` | ERROR | `method`, `url`, `max_retries` | `request_service` |
| `request_complete` | DEBUG | `method`, `status`, `elapsed_ms`, `size` | `http_client` |
| `response_body_truncated` | WARNING | `method`, `url`, `max_bytes` | `http_client` |
| `sse_stream_detected` | DEBUG | `method`, `url`, `content_type` | `http_client` |
| `http_connection_failed` | ERROR | `method`, `url` | `http_client` |
| `http_request_timed_out` | ERROR | `method`, `url` | `http_client` |
| `http_request_failed` | ERROR | `method`, `url`, `detail` | `http_client` |
| `yaml_to_json_conversion_failed` | ERROR | `method`, `url`, `detail` | `http_client` |
| `worker_run_started` | DEBUG | `method`, `url`, `request_id` | `qt/worker` |
| `worker_run_completed` | DEBUG | `method`, `url`, `stopped` | `qt/worker` |
| `worker_run_cancelled` | DEBUG | `method`, `url` | `qt/worker` |
| `worker_stop_requested` | DEBUG | `method`, `url` | `qt/worker` |
| `script_output` | DEBUG | `tab_id`, `line` | worker |
| `script_error` | WARNING | `tab_id`, `error` | worker |
| `stale_worker_cleared` | DEBUG | `method`, `url` | worker |

### Collections and persistence

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `apply_loaded_collections_completed` | INFO | `collection_count`, `request_count` | `request_manager` |
| `delete_request_started` | INFO | `request_id` | `request_manager` |
| `delete_request_succeeded` | INFO | `request_id`, `collection_id` | `request_manager` |
| `delete_request_not_found` | WARNING | `request_id` | `request_manager` |
| `delete_collection_started` | INFO | `collection_id` | `request_manager` |
| `delete_collection_succeeded` | INFO | `collection_id`, `collection_name` | `request_manager` |
| `rename_request_succeeded` | INFO | `request_id`, `new_name` | `request_manager` |
| `rename_collection_succeeded` | INFO | `collection_id`, `new_name` | `request_manager` |
| `collection_item_delete_*` | INFO/WARNING/ERROR | `item_type`, `item_id`, … | tree actions |
| `collection_item_rename_*` | INFO/WARNING/ERROR | `item_type`, `item_id`, `new_name`, … | tree actions |
| `collection_request_opened` | INFO | `request_id`, `request_name` | collections presenter |
| `collection_storage_async_load_dispatched` | INFO | — | async loader |
| `collection_storage_async_load_failed` | ERROR | `error` | async loader |
| `collection_storage_gateway_*` | DEBUG/INFO/WARNING | load lifecycle; finish wait timeout | storage gateway |
| `collection_storage_worker_*` | DEBUG/ERROR | `count`, `error` | storage worker |
| `storage_data_dir_create_failed` | ERROR | `path`, `error` | `storage` |
| `storage_load_failed` | ERROR | `path`, `error` | `storage` |
| `storage_save_failed` | ERROR | `path`, `error` | `storage` |
| `storage_collection_migrated` | INFO | path details | `storage` |
| `storage_encryption_config_applied` | INFO | encryption settings | `storage` |

### Environments

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `load_environments_completed` | INFO | `count` | env presenter |
| `load_environments_failed` | ERROR | `error` | env presenter |
| `environment_deleted` | INFO | `env_name` | env list widget |
| `environment_renamed` | INFO | old/new names | env list widget |
| `environment_copied` | INFO | source/target | env list widget |
| `env_manager_dialog_opened` | INFO | `current_env` | env presenter |
| `env_selected` | INFO | index, name | env presenter |
| `env_deselected` | INFO | `index` | env presenter |
| `env_variable_deleted` | INFO | variable name | env variables widget |
| `env_variable_moved` | INFO | reorder details | env variables widget |
| `env_hidden_flag_changed` | INFO | variable, flag | env variables widget |
| `variable_set_in_env` | INFO | env, name | env presenter |
| `variable_set_request_no_env_selected` | WARNING | — | env presenter |
| `environment_storage_gateway_*` | DEBUG/INFO/WARNING | op, count, elapsed | env gateway |
| `environment_storage_worker_*` | DEBUG/ERROR | op, count, error | env worker |
| `save_environments_completed` | INFO | count | env adapter |
| `save_environments_replace_failed` | ERROR | details | env adapter |

### Encryption and key material

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `encryption_migration_verify_started` | INFO | — | `encryption_migration` |
| `encryption_migration_verify_completed` | INFO/WARNING | `success` | `encryption_migration` |
| `encryption_migration_operation_started` | INFO | operation | `encryption_migration` |
| `encryption_migration_operation_completed` | INFO | counts | `encryption_migration` |
| `encryption_migration_decrypt_failed` | ERROR | `detail` | `encryption_migration` |
| `encryption_migration_worker_started` | INFO | `operation` | migration worker |
| `encryption_key_unavailable` | ERROR | `reason` | `key_provider` |
| `key_source_chain_active_attempt` | INFO | `sources` | `key_sources/chain` |
| `key_source_chain_active_resolved` | DEBUG/INFO | `source`, `key_id` | `key_sources/chain` |
| `key_source_chain_active_fallback` | WARNING | source chain | `key_sources/chain` |
| `env_encryption_key_resolved` | DEBUG | `source`, `key_id` | `key_sources/env` |
| `keyring_encryption_key_match` | DEBUG | `key_id` | `key_sources/keyring` |
| `secret_store_encryption_key_resolved` | DEBUG | `key_id` | `key_sources/secret_store` |
| `webhook_auth_encrypt_failed` | WARNING | `reason` | `settings_secrets` |
| `webhook_auth_decrypt_failed` | ERROR | `reason` | `settings_secrets` |

### MCP

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `mcp_activity_recorded` | INFO | `operation`, `outcome`, `tool_name`, counts, `duration_ms` | `mcp_activity_log` |
| `mcp_activity_cleared` | INFO | `count` | `mcp_activity_log` |
| `mcp_activity_dialog_opened` | INFO | `entry_count` | env presenter |
| `mcp_server_listening` | INFO | `host`, `port` | `qt/mcp_server` |
| `mcp_server_start_failed` | ERROR/exception | `host`, `port`, `message` | `qt/mcp_server` |
| `mcp_server_unexpected_exit` | WARNING | — | `qt/mcp_server` |
| `mcp_tools_changed` | INFO | `tool_count`, `restarting` | `qt/mcp_server` |
| `mcp_operation_start` | DEBUG | `url`, `operation` | `mcp_client_service` |
| `mcp_operation_success` | DEBUG | `url`, `operation`, `elapsed` | `mcp_client_service` |
| `mcp_operation_failed` | ERROR | `url`, `operation`, `category`, `detail` | `mcp_client_service` |
| `mcp_tools_overview_opened` | INFO | `tool_count` | env presenter |

See [mcp_integration.md](mcp_integration.md) for operator workflow.

### Metrics server

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `metrics_server_listening` | INFO | `host`, `port` | `metrics_server` |
| `metrics_server_start_failed` | ERROR/exception | `host`, `port`, `message` | `metrics_server` |
| `metrics_server_unexpected_exit` | WARNING | — | `metrics_server` |
| `metrics_server_non_localhost_bind` | WARNING | `host`, `port` | `metrics_server` |
| `metrics_server_restarting` | INFO | `host`, `port` | `main_window` |
| `metrics_server_start_failed_ui` | ERROR | `message` | `main_window` |

Legacy lifecycle strings (`Metrics server starting on %s:%d`, `Metrics server stopped`) remain
in `metrics_server.py` — migrate when touching that module.

### Alerts

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `alert_emitted` | WARNING | `request_name`, `endpoint`, `retries`, `error_category`, `webhook` | `alert_manager` |
| `alert_manager_reloaded` | INFO | `log_path`, `webhook_url_set` | `main_window` |
| `alert_webhook_ok` | DEBUG | `target`, `status` | `alert_manager` |
| `alert_webhook_failed` | WARNING | `target`, `error` | `alert_manager` |
| `alert_manager_stale_handlers_evicted` | WARNING | `count`, `log_path` | `alert_manager` |

Treat `endpoint` and webhook `target` as potentially sensitive — see
[security_audit.md](security_audit.md).

### History

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `history_entry_appended` | DEBUG | `method`, `url`, `count` | `history_manager` |
| `history_entry_recorded` | DEBUG | `method`, `url`, `status`, `response_time_ms` | `request_service` |
| `history_masking_applied` | DEBUG | `method`, `hidden_key_count` | `request_service` |
| `history_record_failed` | ERROR | `error` | `request_service` |
| `history_cap_enforced` | WARNING | `max` | `history_manager` |
| `history_cleared` | INFO/DEBUG | `count` | panel / manager |
| `history_curl_copied` | INFO | `method`, `url` | history panel |
| `history_load_async_dispatched` | INFO | `path` | `history_manager` |

### Templates

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `template_compile_cache` | DEBUG | `hits`, `misses`, `size` | `template_service_render` |
| `template_expression_render_succeeded` | DEBUG | `render_path`, `token_count` | `template_service_render` |
| `template_expression_validation_failed` | INFO | — | `template_service_render` |
| `template_render_fallback_to_original` | WARNING | `render_path`, `error_type` | `template_service_render` |

### UI actions (tabs, editor, styles)

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `new_tab_action_triggered` | INFO | `source`, `tabs_before` | `tabs_presenter` |
| `restore_tabs_completed` | INFO | `restored_count` | `tabs_presenter` |
| `copy_curl_success` | INFO | `request_id`, `length` | `tabs_presenter` |
| `save_as_flow_started` | INFO | `source_request_id` | save orchestrator |
| `save_request_new_succeeded` | INFO | `request_id`, `name`, `collection_id` | save orchestrator |
| `code_editor_async_paste_*` | DEBUG | `generation`, reason | `code_editor` |
| `response_search_typed` | DEBUG | `query_len`, `matches` | `response_view` |
| `styles_loaded` | DEBUG | `file_count`, `bytes` | `style_manager` |
| `theme_applied` | DEBUG | `theme`, style name | `style_manager` |

### Qt state and async workers

| Event | Level | Key fields | Module |
| --- | --- | --- | --- |
| `state_manager_save_scheduled` | DEBUG | `debounce_ms` | `state_manager` |
| `state_manager_save_debounced` | DEBUG | — | `state_manager` |
| `state_manager_save_immediate` | DEBUG | — | `state_manager` |

## Legacy Migration

Legacy messages fall into three patterns. **Migrate when touching a file** — no big-bang rewrite
required ([PYPOST-751](https://pypost.atlassian.net/browse/PYPOST-751) tracks bulk migration).

### Pattern A — Human-readable error prefix (HTTP client)

**Before (legacy):**

```python
logger.error(
    "Request timed out: %s %s",
    request_data.method,
    url,
)
```

**After (preferred):**

```python
logger.error(
    "http_request_timed_out method=%s url=%r",
    request_data.method,
    self._error_log_url(url, variables),
)
```

Same for `Connection failed:` → `http_connection_failed`, `Request failed:` →
`http_request_failed`. Use `_error_log_url()` for ERROR-level URLs (sanitized per
[PYPOST-741](https://pypost.atlassian.net/browse/PYPOST-741)). Migrated in
[PYPOST-751](https://pypost.atlassian.net/browse/PYPOST-751).

### Pattern B — ClassName: diagnostic prefix

Common in composition-root and worker modules:

```text
HTTPClient: using injected TemplateService id=%d
RequestWorker: propagating TemplateService id=%d
TabsPresenter: alert_manager_injected=%s
MainWindow: alert_manager_injected=%s
MCPServerImpl: creating RequestService for MCP call
```

**After (preferred):**

```text
http_client_template_service_injected id=%d
request_worker_template_service_propagated id=%d
tabs_presenter_alert_manager_injected value=%s
main_window_alert_manager_injected value=%s
mcp_server_impl_request_service_created
```

Drop the `ClassName:` prefix; encode the component in the event name.

### Pattern C — Title Case lifecycle sentences

```text
PyPost starting up
PyPost shutting down
MCP server starting on %s:%d
MCP server stopped
Metrics server starting on %s:%d
Metrics server stopped
Generating cURL for %s %s
```

**After (preferred):**

```text
app_startup
app_shutdown
mcp_server_starting host=%s port=%d
mcp_server_stopped
metrics_server_starting host=%s port=%d
metrics_server_stopped
curl_generated method=%s url=%s
```

Startup/shutdown in `main.py` migrated to `app_startup` / `app_shutdown` ([PYPOST-801](https://pypost.atlassian.net/browse/PYPOST-801)).

### Migration checklist

When editing a module with legacy logs:

1. Pick a **snake_case event name** describing the action (not the class).
2. Move variable context into **`key=value`** pairs after the event name.
3. Keep **`%` formatting**; preserve log level semantics.
4. Update **tests** that assert message prefixes (`caplog`, allowlist YAML if ERROR).
5. For URLs at ERROR/WARNING, use sanitized helpers — never log raw query strings with secrets.

### CI allowlist

ERROR-level legacy prefixes (for example `Connection failed`) are listed in
`tests/expected_log_allowlist.yaml`. When renaming ERROR events, update the allowlist rule
prefix to match the new event name.

## Sensitive Data

| Field | Guidance |
| --- | --- |
| `url`, `endpoint` | Use masked/sanitized forms at WARNING+; DEBUG may include full URLs |
| `key_id` | Safe to log; never log key values |
| MCP args | Log counts only (`mcp_arg_count`), never argument values |
| Webhook auth | Never logged; `webhook=true/false` flag only |

Full matrix: [security_audit.md](security_audit.md) and
[sensitive_data_masking_policy.md](sensitive_data_masking_policy.md).

## Maintaining the Catalog

Regenerate a rough inventory after large logging changes:

```bash
# Count calls by level
rg -o 'logger\.(debug|info|warning|error|exception)' pypost/ | sort | uniq -c

# List unique message prefixes (first string literal)
rg -o 'logger\.(info|debug|warning|error)\(\s*["\x27]([^"\x27]+)' pypost/ -r '$2' | sort -u

# Find legacy ClassName: patterns
rg 'logger\.\w+\(\s*["\'][A-Z][a-zA-Z]+:' pypost/
```

Update this document when adding new domains or stable public events operators rely on.

## Related Documentation

| Document | Topic |
| --- | --- |
| [observability_audit.md](observability_audit.md) | Audit summary, metrics, MCP activity, gaps |
| [agent_lifecycle.md](agent_lifecycle.md) | Agent launch → ready → shutdown (PYPOST-833) |
| [agent_e2e_seed.md](agent_e2e_seed.md) | Agent e2e seeded workspace (PYPOST-857) |
| [agent_e2e.md](agent_e2e.md) | Agent UI e2e packaging + fixtures (PYPOST-858) |
| [agent_e2e_http.md](agent_e2e_http.md) | Deterministic HTTP stubs (PYPOST-859) |
| [agent_e2e_failure_artifacts.md](agent_e2e_failure_artifacts.md) | Failure snapshot dumps (PYPOST-860 / 875 / 876) |
| [testing.md](testing.md) | pytest `log_cli`, CI guardrails |
| [mcp_integration.md](mcp_integration.md) | MCP activity viewer |
| [security_audit.md](security_audit.md) | Secrets in logs |
