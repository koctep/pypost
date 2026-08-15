# PYPOST-1006: Observability Implementation

## Summary

This task is verification debt. Collection import already emits
`collection_import_file_invalid` for both invalid-file reasons (PYPOST-987,
still present after the PYPOST-1005 off-thread parse split). PYPOST-1006
added `caplog` locks for those reasons; it did **not** add or change
production logging or metrics.

## Logging Implementation

### Added Logs

None. No production `logger.*` call was added, renamed, or reformatted.

Existing syslog-compatible coverage for the invalid-file path (unchanged):

- **EMERG**: not applicable — invalid import files are recoverable, per-file
  user outcomes, not system-wide failures.
- **ALERT**: not applicable — no paging condition.
- **CRIT**: not applicable — import never takes down the app on a bad file.
- **ERR**: `pypost/ui/presenters/collection_import_actions.py::_on_parse_failed`
  — `collection_import_parse_unexpected error=%s` for a non-file exception
  from the worker. Out of scope for this ticket (not an invalid-file
  `reason`). Persist-time `collection_import_save_failed` remains in
  `collection_import_apply.py` and is already locked via caplog.
- **WARNING**: `collection_import_actions.py::_on_parse_completed` —
  `collection_import_file_invalid reason=no_valid_collections` when parse
  succeeds with an empty candidate list. Logger:
  `pypost.ui.presenters.collection_import_actions`.
- **WARNING**: `collection_import_actions.py::_on_parse_failed` —
  `collection_import_file_invalid reason=%s` when the worker raises
  `CollectionImportFileError` (`%s` is `str(error)`, the exception message).
  Same event name as the empty-list branch; distinguished only by `reason`.
- **NOTICE**: not used (Python logging has no project-level NOTICE mapping).
- **INFO**: surrounding import events (`collection_import_parse_started`,
  `collection_import_file_parsed`, `collection_import_completed`,
  `collection_import_skipped`) are unchanged and out of this ticket's gap.
- **DEBUG**: worker start/complete and busy-cue lines are unchanged. Tests
  must **not** treat worker `collection_import_parse_worker_failed` as the
  terminal invalid-file event.

### Log Structure

Log format used (pre-existing, unchanged):

- Structured logs: yes — `printf`-style `%s` tokens producing
  `event_name key=value` (same shape as `collection_import_completed` and
  `collection_import_save_failed`).
- Includes context: yes — a short structural `reason` (literal
  `no_valid_collections`, or the file-error message). No collection names,
  request bodies, headers, or URLs.
- Log levels: WARNING for both invalid-file branches.

Both branches share one event name on purpose: they are the same
user-visible "nothing changed" outcome. Operators distinguish them by
`reason`. Asserting only the event name would still allow one reason to be
dropped or swapped; that is the gap this task closed in tests.

File-level parse failures are logged twice on purpose (`doc/dev/collection_import.md`):
worker `collection_import_parse_worker_failed`, then orchestrator
`collection_import_file_invalid`. Zero-usable-collections is **not** a
worker failure: parse returns `[]`, and only the orchestrator emits
`reason=no_valid_collections`.

## Metrics Implementation (if applicable)

Not applicable. This ticket added tests, not a new operation or SLO.

### Performance Metrics

None added. Invalid-file handling is a one-shot user action; no latency or
throughput metric is justified.

### Business Metrics

None added. Invalid-file frequency can already be derived from the existing
WARNING event in log aggregation. No Prometheus counter was introduced in
PYPOST-987, and this follow-up does not add one.

### System Health Metrics

None added. A bad import file is not a component-health signal.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — none added; none exist specifically for invalid
      collection-import files
- [ ] Grafana dashboards — none added
- [ ] Alerting rules — none added (invalid files are user input, not paging)
- [x] Log aggregation (ELK, Loki, etc.) — existing structured WARNING lines
      remain consumable; no format change

## Validation Results

Validation results:

- [x] Logs are correctly formatted — verified by reading
      `collection_import_actions.py` `_on_parse_completed` /
      `_on_parse_failed`; both still emit
      `collection_import_file_invalid reason=…` at WARNING on logger
      `pypost.ui.presenters.collection_import_actions`
- [x] Metrics are collected correctly — N/A, no metrics added
- [x] Logging works in error scenarios — both invalid-file WARNING reasons
      are now asserted via `caplog` (see Tests below). Existing UX tests
      still prove the error dialog and unchanged collections
- [x] Large data structures are not logged — `reason` is either the literal
      `no_valid_collections` or `str(CollectionImportFileError)`; no
      `Collection` / request payload is passed to `logger.warning`
- [ ] Metrics are available for monitoring — N/A, no metrics added

### Tests (this task)

`tests/test_collections_import_ui.py` (`TestImportCollections`), scoped with
`caplog.at_level(logging.WARNING, logger=_MODULE)` where `_MODULE` is
`pypost.ui.presenters.collection_import_actions`:

- `test_logs_file_invalid_on_parse_failure` — WARNING record with
  `collection_import_file_invalid reason=` plus the parse-failure text
  (`not valid JSON` / `boom`); logger name is the orchestrator module (not
  the worker); **no** record contains `reason=no_valid_collections`.
- `test_logs_file_invalid_on_zero_usable_collections` — WARNING record with
  the exact token
  `collection_import_file_invalid reason=no_valid_collections`.

Completed-import and save-failed events were already locked via caplog
(`test_logs_completed_event_with_counts`,
`tests/test_collection_import_apply.py`). Invalid-file is now the same
class of lock.

Apply-to-all (3+ KEEP_BOTH) and copy-name past `(2)` are behavioral locks,
not log/metric changes.

## Notes

PYPOST-987 Step 6 recorded the missing caplog asserts as a low-priority
follow-up (`ai-tasks/PYPOST-987/50-observability.md` Notes,
`ai-tasks/PYPOST-987/60-tech-debt.md` follow-up #4). This ticket closes that
gap in tests only.

No production logging or metrics were required or added. Inventing new
events here would duplicate the existing WARNING pair and would not match
the Definition of Done.

STEP 6 left as `[/]` pending review.
