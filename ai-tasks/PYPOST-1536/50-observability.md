# PYPOST-1536: Observability

## Analysis

This debt fix hardens the non-blocking dialog-init regression test only. Product
logging for manifest discovery is already in place from PYPOST-1424 / 1450 /
1451:

- `collection_variable_import_dialog_opened`
- `collection_variable_manifest_discovery_started` / `_completed` / `_failed` /
  `_cancelled` / `_retry_requested` / `_stale_discarded`
- Worker debug lines in `ManifestDiscoveryWorker`

No new log lines or metrics are required: the contract is enforced by the
Event-gate test, not by runtime telemetry.

## Changes

- N/A — no observability code changes.

## Validation

- Existing dialog/worker INFO/DEBUG events remain unchanged and continue to
  appear in the focused repro’s captured logs when discovery runs.
