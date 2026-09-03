# PYPOST-1228: Observability Implementation

## Logging Implementation

### Existing Logging Reviewed

`pypost/ui/presenters/collection_import_actions.py` already carries structured logging (per its
established convention: lowercase `module_event` message + space-separated `key=value` fields) at
every transition point touched by this refactor:

- `import_collections()` — `INFO collection_import_skipped reason=busy` when the re-entrancy guard
  fires.
- `_start_parse()` — `INFO collection_import_parse_started path=%s`, emitted right after the
  PREPARING→PARSING transition.
- `_on_parse_completed()` — `WARNING collection_import_file_invalid reason=no_valid_collections`
  on the empty-collections branch (state → IDLE).
- `_on_parse_failed()` — `WARNING collection_import_file_invalid reason=%s` for a known
  `CollectionImportFileError`, or `ERROR collection_import_parse_unexpected error=%s` for any other
  exception (state → IDLE in both cases).
- `_finish_import()` — `INFO collection_import_completed added_count=%d updated_count=%d
  skipped_count=%d renamed_count=%d request_count=%d error_count=%d` as its second-to-last
  statement, immediately before the new APPLYING→IDLE transition.
- `teardown()` — `INFO collection_import_teardown_started/_completed`, plus `WARNING`/`DEBUG` for
  the worker interrupt/reap sub-steps.
- `_set_state()` (the single transition helper, née `_set_preparing`) — `DEBUG
  collection_import_busy_cue_shown` / `DEBUG collection_import_busy_cue_cleared`, tied to the
  button-enable/status-message side effects.

### Gap Identified

`_set_state()`'s existing debug log is binary (`busy_cue_shown` vs `busy_cue_cleared`) — it only
distinguishes "some non-idle state" from "idle," collapsing PREPARING, PARSING, and APPLYING into
a single "shown" event indistinguishable from one another in the log stream. This is precisely the
axis this ticket added: the whole point of `CollectionImportState` is to make the previously
implicit PREPARING/PARSING/APPLYING distinction explicit, including the new APPLYING window that
closes the `is_busy()` gap (see `20-architecture.md`). Without a log line naming which state is
being entered, a production log cannot show *that* the APPLYING window is the one in flight, e.g.
when diagnosing a hang or a report of "import button stayed disabled" — the log stream would show
only two indistinguishable "cue shown" events per import (PREPARING and PARSING) with no signal at
all for the APPLYING transition or the gap-closing fix's coverage. This directly reduces
diagnosability of the exact lifecycle-ordering bug class this ticket fixed (the
`_worker`/`_preparing` disagreement was invisible in logs before the fix, and the binary busy-cue
log alone would not make the new four-state machine's actual transitions visible after it either).

### Added Logs

- **DEBUG**: `CollectionImportActions._set_state()` — new line `collection_import_state_changed
  from=%s to=%s`, logging the enum's `.value` (`idle`/`preparing`/`parsing`/`applying`) for both
  the state being left and the state being entered. Fires for every transition: `IDLE→PREPARING`
  (`_start_parse`, before worker construction), `PREPARING→PARSING` (`_start_parse`, after
  `worker.start()`), `PARSING→IDLE` (`_on_parse_completed`'s empty-collections branch and
  `_on_parse_failed`), `PARSING→APPLYING` (`_on_parse_completed`'s valid-collections branch — the
  new state this ticket introduces), `APPLYING→IDLE` (last line of `_finish_import()`), and any
  state `→IDLE` (`teardown()`, unconditional). Placed as the first statement in `_set_state()`, one
  DEBUG line per transition, two scalar string fields only — no collections, paths, or other bulk
  data.

No other logging was added. The existing `INFO`/`WARNING`/`ERROR` calls listed above already cover
the operationally significant events (parse start/completion/failure, apply result counts,
teardown lifecycle) at the level of detail the syslog convention calls for; they needed no change.

### Log Structure

Log format used:

- Structured logs: yes — `event_name key=value key=value ...`, matching every other log call in
  this file (e.g. `collection_import_completed added_count=%d ...`).
- Includes context: yes — the new line names both endpoints of the transition (`from`/`to`), which
  is the minimal context needed to reconstruct the state-machine's path through a given import from
  the log stream alone.
- Log levels used in this file (unchanged set): `DEBUG`, `INFO`, `WARNING`, `ERROR`.

## Metrics Implementation (if applicable)

Not applicable. This is a UI-thread presenter state machine inside a desktop application; there is
no metrics/monitoring pipeline (Prometheus, Grafana, etc.) wired into this codebase's `pypost/ui`
layer, and none of the sibling presenter files (`collection_export_actions.py`,
`collections_async_loader.py`, `tabs_presenter*.py`) emit metrics either — logging is this
codebase's sole observability channel for presenter-level lifecycle events.

## Monitoring Integration

- [ ] Prometheus metrics — N/A, no metrics pipeline in this codebase
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A, desktop application; logs go to the standard Python
      logging handlers configured elsewhere in the app, unchanged by this ticket

## Validation Results

- [x] Logs are correctly formatted — `collection_import_state_changed from=%s to=%s` follows the
      file's existing `event_name key=value` convention exactly.
- [x] Large data structures are not logged — only two short enum-value strings per line.
- [x] Logging works in error scenarios — the `PARSING→IDLE` transition fires (and is now logged)
      on both the `_on_parse_completed` empty-collections branch and `_on_parse_failed`, alongside
      the pre-existing `WARNING`/`ERROR` calls on those same paths.
- [x] Targeted regression suite re-run after the change: `tests/test_collections_import_ui.py`,
      `tests/test_collection_import_teardown_repro.py`, `tests/test_collection_import_async_gaps.py`
      — 30 passed (`QT_QPA_PLATFORM=offscreen .venv/bin/pytest ...`). Existing substring-based
      `caplog` assertions on `collection_import_busy_cue_shown`/`_cleared`,
      `collection_import_parse_started`, and `collection_import_completed` still pass unchanged —
      the new DEBUG line is additive and does not alter any pre-existing message text.
- [ ] Metrics are collected correctly — N/A, no metrics added (see above).

## Notes

- The new log line is DEBUG-level, matching the pre-existing `busy_cue_shown`/`busy_cue_cleared`
  DEBUG calls it sits next to in `_set_state()` — it is diagnostic detail for developers/support
  investigating lifecycle issues, not an operator-facing INFO/WARNING/ERROR event, consistent with
  how the rest of this file reserves INFO+ for user-visible or otherwise operationally significant
  events (parse start, completion counts, teardown, failures).
- No test asserts on the new `collection_import_state_changed` line specifically; it was verified
  manually to appear via the targeted `caplog.at_level(logging.DEBUG)` runs in
  `tests/test_collections_import_ui.py::test_logs_completed_event_with_counts` and
  `tests/test_collection_import_teardown_repro.py::test_teardown_structured_logging` (both already
  pass `DEBUG` level and inspect `caplog.records`, so the new lines are present in their captured
  output — the tests just don't specifically assert on this new message, only on the messages that
  predate this ticket, which remains correct since it's additive).
