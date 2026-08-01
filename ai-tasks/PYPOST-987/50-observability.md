# PYPOST-987: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging was written during Step 4 alongside the code, following the
project's existing `key=value` / `*_parsed`, `*_completed`, `*_failed`,
`*_invalid` convention (`save_environments_completed`,
`apply_loaded_collections_completed`, `environment_import_completed`). This
step verifies and documents that coverage; no log call was added or changed
here.

The design goal is that **every terminal branch of an import emits exactly one
summarizing line**, so an operator reading a log can always answer "was a file
picked, did anything change, and what went wrong" without reconstructing state.

- **INFO**: `pypost/core/collection_import.py::load_collection_import_candidates`
  (line 146) — `collection_import_file_parsed path=%s candidate_count=%d
  error_count=%d`. Emitted whenever an import file is read and decoded,
  regardless of whether individual records failed, so "a file was picked" can
  be correlated with "how many usable collections and how many rejected
  records it contained".
- **WARNING**:
  `pypost/ui/presenters/collection_import_actions.py::_load` (line 114) —
  `collection_import_file_invalid reason=%s` when `CollectionImportFileError`
  is raised (unreadable file, malformed JSON, a root that is neither a list nor
  an object, or a list element that is not an object). `reason` is the
  exception message, which carries only structural detail — never request
  headers, bodies, or URLs.
- **WARNING**: same method (line 119) —
  `collection_import_file_invalid reason=no_valid_collections` when the file
  parses without a hard error but yields zero usable collections. It reuses the
  same event name as the hard-failure case above because both are "nothing
  changed" outcomes for the user, and is distinguished only by `reason` —
  matching the precedent set by `environment_import_file_invalid`.
- **INFO**: `pypost/core/collection_import_apply.py::apply_imported_collections`
  (line 63) — `collection_import_applied collection_count=%d
  persisted_count=%d failed_count=%d`. This is the *storage-layer* view: how
  many collections the app now holds, how many files were written, and how many
  writes failed. It is distinct from the flow-level completion line below
  because a caller can apply a plan without going through the UI.
- **INFO**:
  `pypost/ui/presenters/collection_import_actions.py::import_collections`
  (line 87) — `collection_import_completed added_count=%d updated_count=%d
  skipped_count=%d renamed_count=%d request_count=%d error_count=%d`. The
  primary operational signal for a completed import. `request_count` is the
  collection-specific addition to the environment-import shape, since a single
  imported collection can carry an arbitrary number of requests and "3
  collections" alone understates the size of the change.
- **ERR**: `pypost/core/collection_import_apply.py::apply_imported_collections`
  (line 54) — `collection_import_save_failed collection_id=%s error=%s` when
  `StorageManager.save_collection` raises `OSError` (disk full, permissions,
  read-only data directory). Logged **per failing collection**, and the loop
  deliberately continues so one bad write cannot strand the remaining
  collections. This is ERR rather than WARNING because in-memory state and
  on-disk state have genuinely diverged at that point, which is an operator
  concern, not merely a user-input problem. The collection **id** is logged
  rather than its name, keeping user-authored text out of the log.
- **EMERG / ALERT / CRIT**: not applicable. Every import failure is a
  recoverable, user-facing, per-file or per-collection outcome; none represents
  a system-level failure requiring immediate operator intervention.
- **NOTICE / DEBUG**: not used, consistent with the surrounding collection
  actions (create / rename / delete in `request_manager.py` and
  `collection_tree_actions.py`), none of which define a NOTICE or DEBUG tier.

### Log Structure

Log format used:

- Structured logs: yes — `printf`-style `%s`/`%d` placeholders producing
  `key=value` tokens, identical in shape to `apply_loaded_collections_completed`
  and the PYPOST-986 import lines.
- Includes context: yes — the file path at parse time, a short structural
  reason on failure, a collection id on a failed write, and integer counts
  everywhere else.
- Log levels used: INFO, WARNING, ERROR.

**Deliberately never logged:** request URLs, headers, bodies, pre/post scripts,
MCP descriptions and parameter schemas, and collection or request *names*. An
imported collection routinely contains credentials in a header template or a
token in a URL, so the import path logs only counts, ids, and structural
reasons. The one place a user-authored name reaches the user is the result
dialog and the returned `parse_errors` strings — the UI surface, not the log.

## Metrics Implementation (if applicable)

### Performance Metrics

Not applicable. Import is a synchronous, user-initiated, one-shot action
(pick → parse → prompt → apply → refresh) with no latency-sensitive or
high-throughput path. `CollectionsPresenter` does hold a
`MetricsTrackerProtocol`, but it is used for GUI action counters on tree
interactions; the existing create / rename / delete collection actions do not
register dedicated metrics either, and adding one only for import would be
inconsistent.

### Business Metrics

Not applicable. Neither `10-requirements.md` nor `20-architecture.md` asked for
one, and the counts already carried by `collection_import_completed`
(added / updated / skipped / renamed / requests / errors) let a log-aggregation
pipeline derive import frequency and success rate without a separate counter.

### System Health Metrics

Not applicable. Import writes through the unchanged
`StorageManager.save_collection`, whose own behavior and failure reporting are
untouched by this task.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable (see above)
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation (ELK, Loki, etc.) — the structured `key=value`
      INFO/WARNING/ERROR lines are consumable by the same pipeline as every
      other PyPost operation; no new format was introduced.

## Validation Results

Validation results:

- [x] Logs are correctly formatted — all five event names follow the
      established `key=value` convention; verified by reading
      `collection_import.py:146`, `collection_import_apply.py:54,63`, and
      `collection_import_actions.py:87,114,119`.
- [x] Logging works in error scenarios — the write-failure path is asserted
      through `caplog` in
      `tests/test_collection_import_apply.py::test_write_failure_is_reported_and_does_not_abort_remaining_writes`,
      which checks both that `collection_import_save_failed` is emitted at ERROR
      and that the remaining collections are still written.
- [x] The completion line's exact format is asserted through `caplog` in
      `tests/test_collections_import_ui.py`, which matches on the literal
      `collection_import_completed added_count=1` prefix rather than on a
      substring of the event name alone.
- [x] Large data structures are not logged — confirmed by inspection: every
      call passes only a path, a short exception message, a collection id, or
      integer counts. No `Collection`, `RequestData`, header dict, or body
      string is ever passed to a logging call in the import path.
- [ ] Metrics are available for monitoring — N/A, no metrics added.

## Notes

The `collection_import_file_invalid` WARNING pair is exercised by
`tests/test_collections_import_ui.py` (hard parse failure and the
zero-usable-collections case both assert the user-facing error dialog and that
app state is untouched), but only the *behavior* is asserted there, not the log
text. That is a deliberate, narrow gap: the two branches share one event name,
so a `caplog` assertion would mostly restate the `reason` literal. It is
recorded as a low-priority follow-up in `60-tech-debt.md` rather than left
undocumented.
