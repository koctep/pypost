# PYPOST-446: Technical Debt Analysis

## Shortcuts Taken

- Runtime dependency provisioning for tests was not completed in this environment, so full suite
  execution could not be validated end-to-end during implementation.
- ~~History masking fallback in `RequestService` currently stores raw request templates when
  `TemplateService` is not injected.~~ **Fixed**: `_masking_policy` is now always created using a
  fallback `TemplateService()` when none is injected, so rendered URLs/headers/body are always
  stored in history.

## Code Quality Issues

- `pypost/core/request_service.py`
  - The history-recording branch now combines orchestration, masking, metrics, and logging in one
    method section, making it harder to read and maintain.
  - Suggested improvement: extract helper(s) for history field building and observability emission.
- `pypost/core/sensitive_data_masking_policy.py`
  - Policy currently uses a fixed placeholder (`***`) and inline header rendering logic.
  - Suggested improvement: make placeholder configurable and split rendering into smaller methods.

## Missing Tests

- No integration/UI-level test currently verifies that masked values shown in History panel remain
  masked across persistence-reload cycle under real application wiring.
- No explicit negative test confirms metric `hidden_value_masks_applied_total` is not incremented
  when `hidden_keys` is empty. **Closed:** [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464).
- Full regression run for the whole project test suite is pending due to missing local dependencies
  (`pytest`, `pydantic`, `PySide6`, `requests`, `jinja2`, `platformdirs`).

## Performance Concerns

- Per-request masking renders URL/headers/body with a copied variable map. For typical payloads this
  is low overhead, but requests with very large templated bodies may incur measurable extra CPU.
- Metric label usage is controlled (`surface` low cardinality), so no immediate Prometheus
  cardinality risk is expected from this task's additions.

## Follow-up Tasks

- Add integration test covering hidden-value masking through execution -> history save -> reload ->
  history panel display. Jira: [PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462)
  (Priority: High, Type: Debt).
- Refactor `RequestService.execute` history-recording block into dedicated helpers to reduce method
  complexity. Jira: [PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463) (Priority:
  Normal/Medium, Type: Debt).
- Add explicit tests for masking metric behavior with empty vs non-empty `hidden_keys`. Jira:
  [PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464) (Priority: Normal/Medium, Type:
  Debt). **Done** — see `tests/test_history_masking_metrics.py`.
- Provision CI/local test environment with required dependencies and run full regression for this
  task before merge. Jira: [PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465) (Priority:
  Low, Type: Debt).
