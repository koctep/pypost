# Test log ERROR/WARN inventory

- Total entries: **210** (ERROR: 72, WARNING: 138)

## Summary by logger

| Logger | Total | ERROR | WARNING | Suggested tag |
| --- | ---: | ---: | ---: | --- |
| `pypost.core.request_service` | 61 | 19 | 42 | expected |
| `pypost.core.template_service` | 39 | 0 | 39 | expected |
| `pypost.core.alert_manager` | 28 | 0 | 28 | expected |
| `pypost.core.encryption_migration` | 12 | 6 | 6 | expected |
| `pypost.core.key_provider` | 12 | 12 | 0 | suspicious |
| `pypost.ui.presenters.collection_tree_actions` | 7 | 3 | 4 | expected |
| `pypost.core.key_sources.chain` | 6 | 0 | 6 | unknown |
| `pypost.core.storage` | 6 | 6 | 0 | expected |
| `pypost.ui.presenters.tabs_presenter` | 6 | 6 | 0 | expected |
| `pypost.core.environment_secrets_codec` | 5 | 5 | 0 | suspicious |
| `pypost.core.http_client` | 5 | 5 | 0 | unknown |
| `pypost.core.mcp_client_service` | 4 | 4 | 0 | expected |
| `pypost.core.request_manager` | 4 | 0 | 4 | unknown |
| `pypost.core.encryption_config` | 3 | 0 | 3 | expected |
| `pypost.core.environment_storage_worker` | 2 | 2 | 0 | suspicious |
| `pypost.core.history_manager` | 2 | 0 | 2 | unknown |
| `pypost.core.key_sources.secret_store` | 2 | 0 | 2 | unknown |
| `pypost.ui.presenters.env_presenter` | 1 | 1 | 0 | unknown |
| `pypost.core.environment_storage_gateway` | 1 | 0 | 1 | suspicious |
| `pypost.core.key_sources.registry_validation` | 1 | 0 | 1 | unknown |
| `asyncio` | 1 | 1 | 0 | unknown |
| `pypost.core.environment_variables_adapter` | 1 | 1 | 0 | unknown |
| `pypost.core.worker` | 1 | 1 | 0 | expected |

## Message groups (top 30)

- **25×** `pypost.core.template_service` [WARNING] tag=expected: `template_render_fallback_to_original render_path=runtime error_type=ValueError t`
  - tests: tests/test_http_client.py::TestHTTPClientFunctionExpressions::test_invalid_function_expression_passthrough_in_params, te
- **24×** `pypost.core.alert_manager` [WARNING] tag=expected: `alert_emitted request_name='test-req' endpoint='http://example.com/api' retries=`
  - tests: tests/test_alert_manager.py::TestAlertManagerAccumulation::test_no_accumulation_via_close, tests/test_alert_manager.py::
- **12×** `pypost.core.request_service` [WARNING] tag=expected: `retryable_error method=GET url='http://example.com' category=ErrorCategory.NETWO`
  - tests: tests/test_retry.py::TestExhaustionAlert::test_alert_manager_emit_called_on_exhaustion, tests/test_retry.py::TestExhaust
- **12×** `pypost.core.request_service` [ERROR] tag=expected: `request_execution_failed method=GET url='http://example.com' category=ErrorCateg`
  - tests: tests/test_retry.py::TestBodyErrorNonRetryable::test_body_error_no_retry_metrics, tests/test_retry.py::TestBodyErrorNonR
- **11×** `pypost.core.template_service` [WARNING] tag=expected: `template_render_fallback_to_original render_path=hover error_type=ValueError tok`
  - tests: tests/test_template_service.py::TestTemplateServiceObservability::test_render_invalid_spacing_validation_failure_tracks_
- **9×** `pypost.core.request_service` [WARNING] tag=expected: `retry_exhausted method=GET url='http://example.com' request_name='New Request' r`
  - tests: tests/test_retry.py::TestExhaustionAlert::test_alert_manager_emit_called_on_exhaustion, tests/test_retry.py::TestExhaust
- **8×** `pypost.core.request_service` [WARNING] tag=expected: `retryable_status method=GET url='http://example.com' status=503 attempt=0 max_re`
  - tests: tests/test_retry.py::TestRetryCallback::test_no_callback_does_not_raise, tests/test_retry.py::TestRetryCallback::test_re
- **6×** `pypost.core.request_service` [ERROR] tag=expected: `request_execution_failed method=GET url='http://x' category=ErrorCategory.NETWOR`
  - tests: tests/test_request_service.py::TestRequestServiceErrorHandling::test_execution_error_from_http_client_returns_execution_
- **4×** `pypost.core.request_service` [WARNING] tag=expected: `retry_exhausted method=GET url='http://x' request_name='New Request' retries=0 e`
  - tests: tests/test_request_service.py::TestRequestServiceErrorHandling::test_execution_error_from_http_client_returns_execution_
- **4×** `pypost.core.storage` [ERROR] tag=expected: `load_environments_failed file=/private/var/folders/nw/j_4q1l450l39rp9x46khjp6c00`
  - tests: tests/test_storage_environments.py::test_load_environments_unchanged_on_partial_failure, tests/test_storage_environments
- **3×** `pypost.core.encryption_migration` [WARNING] tag=expected: `encryption_migration_verify_completed success=false error_count=1`
  - tests: tests/test_encryption_migrate_cli.py::test_cli_verify_json_includes_errors, tests/test_encryption_migration.py::test_ver
- **3×** `pypost.core.encryption_config` [WARNING] tag=expected: `encryption_key_source_unsupported source=<MagicMock name='mock.load_config().env`
  - tests: tests/test_main_window.py::TestMainWindow::test_main_window_curl_copied_status_bar
- **3×** `pypost.core.mcp_client_service` [ERROR] tag=expected: `mcp_operation_failed url=http://localhost:1080/sse operation=list_tools category`
  - tests: tests/test_mcp_client_service.py::MCPClientServiceTests::test_connect_error_raises_execution_error_network, tests/test_m
- **3×** `pypost.core.request_service` [WARNING] tag=expected: `retryable_status method=GET url='http://example.com' status=503 attempt=1 max_re`
  - tests: tests/test_retry.py::TestRetryMetrics::test_track_retry_attempt_called_on_each_retry, tests/test_retry.py::TestRetryOnRe
- **2×** `pypost.core.alert_manager` [WARNING] tag=expected: `alert_manager_stale_handlers_evicted count=1 log_path=/var/folders/nw/j_4q1l450l`
  - tests: tests/test_alert_manager.py::TestAlertManagerAccumulation::test_no_accumulation_via_gc_id_reuse, tests/test_alert_manage
- **2×** `pypost.ui.presenters.collection_tree_actions` [WARNING] tag=expected: `collection_item_rename_rejected_empty item_type=request item_id=r1`
  - tests: tests/test_collection_tree_actions.py::TestCollectionTreeActionsIsolated::test_rename_rejected_empty_shows_warning, test
- **2×** `pypost.core.encryption_migration` [ERROR] tag=expected: `encryption_migration_missing_kids count=1`
  - tests: tests/test_encryption_migrate_cli.py::test_cli_verify_json_includes_errors, tests/test_encryption_migration.py::test_ver
- **2×** `pypost.core.encryption_migration` [ERROR] tag=expected: `encryption_migration_data_quality_errors count=1`
  - tests: tests/test_encryption_migration.py::test_bulk_re_encrypt_aborts_on_invalid_hidden, tests/test_encryption_migration.py::t
- **2×** `pypost.core.key_sources.chain` [WARNING] tag=unknown: `key_source_chain_by_id_fallback failed_source=keyring key_id=eb0e6b4f3b4619a4 ne`
  - tests: tests/test_encryption_migration_key_sources.py::test_bulk_re_encrypt_keyring_primary_rotates_active_kid
- **2×** `pypost.core.key_provider` [ERROR] tag=suspicious: `encryption_key_rotation_lookup_failed key_id=eb0e6b4f3b4619a4 reason=no_source_p`
  - tests: tests/test_encryption_migration_key_sources.py::test_bulk_re_encrypt_keyring_primary_rotates_active_kid
- **2×** `pypost.core.http_client` [ERROR] tag=unknown: `Connection failed: GET http://x`
  - tests: tests/test_http_client.py::TestHTTPClientSendRequest::test_connection_error_raises_execution_error_network, tests/test_h
- **2×** `pypost.core.key_provider` [ERROR] tag=suspicious: `encryption_key_unavailable reason=no_source_provided_active_key`
  - tests: tests/test_storage_environments.py::test_metrics_track_save_encryption_error_when_key_missing
- **1×** `pypost.core.alert_manager` [WARNING] tag=expected: `alert_webhook_failed url='http://hooks.example.com/alert' error=unreachable`
  - tests: tests/test_alert_manager.py::TestAlertManagerWebhook::test_webhook_failure_does_not_propagate
- **1×** `pypost.core.alert_manager` [WARNING] tag=expected: `alert_webhook_failed url='http://hooks.example.com/alert' error=timed out`
  - tests: tests/test_alert_manager.py::TestAlertManagerWebhook::test_webhook_timeout_does_not_propagate
- **1×** `pypost.ui.presenters.collection_tree_actions` [ERROR] tag=expected: `collection_item_delete_failed item_type=collection item_id=c1 error=disk full`
  - tests: tests/test_collection_tree_delete_metrics.py::TestCollectionTreeDeleteMetrics::test_collection_delete_error_records_erro
- **1×** `pypost.ui.presenters.collection_tree_actions` [WARNING] tag=unknown: `collection_item_delete_not_found item_type=collection item_id=c1`
  - tests: tests/test_collection_tree_delete_metrics.py::TestCollectionTreeDeleteMetrics::test_collection_delete_not_found_records_
- **1×** `pypost.ui.presenters.collection_tree_actions` [ERROR] tag=expected: `collection_item_delete_failed item_type=collection item_id=c1 error=boom`
  - tests: tests/test_collection_tree_delete_metrics.py::TestCollectionTreeDeleteMetrics::test_delete_error_does_not_emit_succeeded
- **1×** `pypost.ui.presenters.collection_tree_actions` [ERROR] tag=expected: `collection_item_delete_failed item_type=request item_id=r1 error=permission deni`
  - tests: tests/test_collection_tree_delete_metrics.py::TestCollectionTreeDeleteMetrics::test_request_delete_error_records_error_m
- **1×** `pypost.ui.presenters.collection_tree_actions` [WARNING] tag=unknown: `collection_item_delete_not_found item_type=request item_id=r1`
  - tests: tests/test_collection_tree_delete_metrics.py::TestCollectionTreeDeleteMetrics::test_request_delete_not_found_records_not
- **1×** `pypost.core.key_sources.chain` [WARNING] tag=unknown: `key_source_chain_active_fallback failed_source=keyring next_source=environment`
  - tests: tests/test_encryption_config.py::test_build_key_provider_keyring_unavailable_falls_back_to_env
