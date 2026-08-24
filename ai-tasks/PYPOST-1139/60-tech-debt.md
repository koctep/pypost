# PYPOST-1139: Technical Debt Analysis

**Verdict:** TD-1 from PYPOST-1129 closed. Per-client messaging (`send_to_client`) and prompt disconnect reclamation (`deleteLater`) delivered with focused tests. **SAFE TO CLOSE.**

## Shortcuts Taken

None for this 1 SP task. Implementation reuses existing `_send_client_text` / `_send_client_binary` helpers and follows established disconnect-handler patterns.

## Code Quality Issues

1. **`deleteLater()` not applied in `drop_clients()` or `stop()`**:
   - Normal disconnect path now calls `deleteLater()`; abrupt `drop_clients()` and bulk `stop()` still close/abort without explicit per-peer `deleteLater()`.
   - *Impact:* Low — churn under normal close is covered; abrupt drops clear the list immediately.
   - *Follow-up:* Optional symmetry in a future harness hardening story if churn tests expand.

## Missing Tests

| Scenario | Status | Notes |
| -------- | ------ | ----- |
| Selective per-client text delivery (multi-peer) | **Present** | `test_send_to_client_selective_delivery` |
| Selective per-client binary delivery | **Present** | Same test, second peer |
| `deleteLater()` on normal disconnect | **Present** | `test_disconnect_invokes_delete_later` |
| `send_to_client` no-op for stale/invalid peer | Deferred | Silent no-op by design; low risk for 1 SP |
| High-churn multi-client stress | Deferred | Existing `test_repeated_startup_teardown_leak_free` covers server cycles |

### Timeout Marker Review

- **BLOCKER Check**: New tests declare `@pytest.mark.timeout(10)`; module-level `pytestmark` retained.
- **Result**: **NO BLOCKER**

## Performance Concerns

None. `send_to_client` is O(1) membership check plus single send; `deleteLater()` is standard Qt deferred cleanup with negligible overhead vs existing disconnect handling.

## Follow-up Tasks

| Item | Priority | Notes |
| ---- | -------- | ----- |
| PYPOST-1140 / TD-2: `max_history` buffer truncation | Low | Pre-existing from PYPOST-1129 |
| `deleteLater()` in `drop_clients()` | Low | Optional harness symmetry |
| Comprehensive multi-session routing test suites | Medium | Downstream WebSocket stories (not 1 SP) |

### Pre-existing test failures (NON-BLOCKER)

Full suite `make test` may report failures unrelated to this task:
- `tests/test_metrics_protocol.py::test_metrics_manager_satisfies_tracker_protocol`
- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
- `tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`
- `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside`
- `tests/test_ui_wait.py` (segfault, exit -11)
