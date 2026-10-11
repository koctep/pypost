# PYPOST-1355: Observability Implementation

## Logging Implementation

The canonical creation helper already emits the necessary lifecycle events introduced in
Step 4. This step adds existing-workspace/request counts to admission and final workspace
count to success, and verifies their contracts. Logging remains in helpers; no presenter
size cap was increased.

| Event | Level | Safe fields and meaning |
| --- | --- | --- |
| `workspace_collection_creation_rejected` | INFO | Fixed `reason`: `teardown`, `import_busy`, or `load_busy`; no write was admitted. |
| `workspace_collection_creation_admitted` | INFO | Fresh `collection_id`, `existing_count`, `request_count`; save is about to run. |
| `workspace_collection_creation_succeeded` | INFO | `collection_id`, `request_count`, `collection_count`; saving and canonical publication completed. |
| `workspace_collection_creation_failed` | WARNING | Fresh `collection_id`, fixed `reason=save`; copy was not published. |
| `workspace_collection_cleanup_failed` | ERROR | Fresh `collection_id`; the attempt to remove the new partial file also failed. |
| `builtin_collection_copy_failed` | WARNING | Fixed `reason=load` or `reason=create`; the editor retains its selection and shows safe retry feedback. |

Events use the existing Python logging configuration and structured `key=value` messages.
The owner logger is `pypost.ui.presenters.collections_presenter_creation`; editor feedback
uses `pypost.ui.mcp_builtin_collection_copy`. New diagnostics include no collection names,
request payloads, URLs, headers, presets, variable values, secrets, raw exception text, or
traceback attachment. The original save exception remains the synchronous caller's outcome;
cleanup failure cannot replace it. The editor translates exceptions to a fixed safe message.

## Metrics Implementation

No new metric schema, counter, exporter, dashboard, or alert is needed for this bounded local
editor operation. Existing application metrics and logging infrastructure remain in use.
Request/workspace counts in lifecycle logs provide the diagnostic context needed here;
there is no measured latency regression or service-level indicator requiring instrumentation.
Collection IDs are used for log correlation rather than high-cardinality metric labels.

## Validation Results

Strengthened existing tests without changing their behavioral requirements or item count:

- Success asserts the exact admission/success events and counts, with no private description,
  header/body sentinel, collection name, or request URL present in the owner diagnostics.
- Busy load/import and teardown assert their exact rejection reason and absence of admission
  or success events.
- Save failure asserts its structured failure event, no false cleanup-failure event, no raw
  credential-like exception text, and successful retry after narrow cleanup.
- Simultaneous save/delete failure asserts the exact ERROR cleanup event, fresh ID correlation,
  absence of `exc_info` and success diagnostics, preservation of the original exception,
  no canonical/tree publication or editor switch, and no private exception text in logs/UI.

`make test PYTEST_ARGS='tests/test_mcp_builtin_collection_copy.py
tests/test_mcp_builtin_paired_env.py tests/test_mcp_servers_dialog.py
tests/test_collections_presenter.py -q'` passed all four modules, including all 16 collection
copy repro items. Log: `/tmp/pypost1355-step6-tests.log`.

`make lint typecheck check-baseline-metrics` passed. The mypy baseline remains 181 known
errors and module/class caps remain unchanged. Log: `/tmp/pypost1355-step6-quality.log`.
The tests retain explicit 30-second module timeout and bounded fixture teardown.

## Notes

The full suite was not repeated for these diagnostic field/assertion changes. Previously
classified failures remain linked in the [roadmap](00-roadmap.md) under PYPOST-1298/1299,
PYPOST-1361, and PYPOST-1362. Step 6 remains in progress for independent acceptance review.
