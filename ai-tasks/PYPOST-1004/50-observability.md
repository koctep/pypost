# PYPOST-1004: Observability Implementation

## Logging Implementation

### Decision

Approach C (reload memory from durable storage when any import save fails) adds a
**new recovery branch** that was silent after Step 4. Existing
`collection_import_save_failed` (ERROR, per collection) and
`collection_import_applied` (INFO, with `failed_count`) still describe write
failures and the apply summary, but neither states that reconciliation ran.
Operators correlating "sidebar matches disk after an unsuccessful import" need
an explicit event when `reload_collections()` executes.

**New logging:** one WARNING line immediately after the reload.
**Metrics:** none (same rationale as PYPOST-987 — sync, user-initiated,
one-shot path; counts already ride on structured logs).

### Added Logs

- **WARNING**: `pypost/core/collection_import_apply.py::apply_imported_collections`
  — `collection_import_reconciled failed_count=%d collection_count=%d` after
  `manager.reload_collections()` when `failures` is non-empty.
  - `failed_count`: number of collections that raised `OSError` during persist
    (same length as the returned failure list).
  - `collection_count`: post-reload in-memory size via
    `len(manager.get_collections())` — durable-aligned membership, not the
    planned list.
  - WARNING (not INFO) so recovery is distinct from the always-emitted
    `collection_import_applied` INFO line and easy to filter in log aggregation.
  - Happy path does not emit this event (no reload).

### Unchanged (still required for this path)

- **ERR**: `collection_import_save_failed collection_id=%s error=%s` — per
  failed write; unchanged from PYPOST-987.
- **INFO**: `collection_import_applied collection_count=%d persisted_count=%d
  failed_count=%d` — still emitted after the failure/reconcile branch;
  `collection_count` here remains the **planned** list length passed into
  apply (pre-reconcile argument), while the WARNING line's `collection_count`
  is post-reload. Do not treat them as the same field across events.
- **INFO**: UI `collection_import_completed …` — unchanged; plan counts +
  `error_count` (dialog contract B).

- **EMERG / ALERT / CRIT / NOTICE / DEBUG**: not used for this task.

### Log Structure

Log format used:

- Structured logs: yes — `key=value` via `%s`/`%d`, matching
  `collection_import_save_failed` / `collection_import_applied`
- Includes context: yes — failure count and post-reload collection count only
- Log levels used: WARNING (new), plus existing ERROR / INFO on the same path

**Deliberately never logged:** collection/request names, URLs, headers, bodies,
scripts, or full `Collection` objects. Ids appear only on the pre-existing
per-write ERROR line.

## Metrics Implementation (if applicable)

### Performance Metrics

Not applicable. Reconcile is a single `reload_collections()` call on the
failure path only; happy path has zero extra I/O. No latency budget beyond the
existing NFR that successful imports must not become slower.

### Business Metrics

Not applicable. Frequency of mid-write recovery can be derived from
`collection_import_reconciled` WARNING volume (and from
`collection_import_applied` with `failed_count > 0`) without a separate counter.

### System Health Metrics

Not applicable. Storage health remains surfaced by per-collection
`collection_import_save_failed` ERROR lines.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable (optional future: alert on sustained
      `collection_import_reconciled` rate if disk/permission issues recur)
- [x] Log aggregation (ELK, Loki, etc.) — structured `key=value` WARNING is
      consumable by the same pipeline as other PyPost operations

## Validation Results

Validation results:

- [x] Logs are correctly formatted — inspected
      `pypost/core/collection_import_apply.py` for the new WARNING and retained
      ERROR/INFO events
- [x] Metrics are collected correctly — N/A
- [x] Logging works in error scenarios — asserted via `caplog` at WARNING in
      `tests/test_collection_import_apply.py`:
      - `test_write_failure_is_reported_and_does_not_abort_remaining_writes`
        expects `collection_import_reconciled failed_count=1`
      - `test_mid_write_save_failure_reconciles_memory_to_durable_storage`
        expects `collection_import_reconciled failed_count=1 collection_count=2`
      - `test_successful_multi_collection_import_does_not_reload` asserts the
        reconcile event is absent
- [x] Large data structures are not logged — only integer counts on the new line
- [ ] Metrics are available for monitoring — N/A

## Notes

`doc/dev/collection_import.md` still describes pre-1004 troubleshooting ("memory
ahead of disk until the next successful save"). Updating that table and listing
the new WARNING event belongs to Step 8 (Dev Docs), not this step.

Operator reading order on mid-write failure:

1. One or more ERROR `collection_import_save_failed` lines
2. WARNING `collection_import_reconciled` (reload ran; memory now durable-sized)
3. INFO `collection_import_applied` with `failed_count > 0`
4. INFO `collection_import_completed` with `error_count > 0` (UI)

## Worklog

```
tokens_used: 22000
role: execution
step: 6
step_name: Observability
```
