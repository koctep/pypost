# PYPOST-1089: Observability Implementation

## Logging Implementation

### Error/Validation Paths Traced

This task added two error paths:

1. `McpToolParam._validate_default_type()` (`pypost/models/models.py`) — raises
   `ValueError` from `model_post_init` when `default`'s Python type doesn't match
   the declared `type` (`None` always allowed). Pydantic wraps this into a
   `pydantic.ValidationError` at `McpToolParam(...)` construction time.
2. `McpParamsTable._parse_default()` (`pypost/ui/widgets/request_editor.py`) —
   dispatches to a `_COERCERS[param_type]` callable to turn the Default cell's
   raw text into a typed value; on `ValueError`/`TypeError`/`json.JSONDecodeError`
   it swallows the exception and falls back to `default=None` (row stays usable,
   nothing crashes).

### Where path (1) surfaces in production

`McpToolParam` is nested inside `RequestData.mcp_params`, which is nested inside
`Collection.requests`. Every place in the codebase that constructs a `Collection`
(and therefore transitively a `McpToolParam`) from **untrusted/external** data
already has an existing `except ValidationError` handler, predating this task,
that this task's new validator now also flows through automatically:

- `pypost/core/storage.py::StorageManager.load_collections()` (line ~153) —
  reads each `collections/<id>.json` file at startup; catches
  `(OSError, json.JSONDecodeError, ValidationError)` per file and logs
  `logger.warning("storage_collection_load_failed filename=%s error=%s", filename, e)`,
  then skips that file (does not crash the app, does not raise a UI dialog for
  this specific path — consistent with how it already handles any other
  malformed collection file, e.g. bad `RetryPolicy` fields).
- `pypost/core/collection_import.py::load_collection_import_candidates()`
  (line ~141) — reads a user-selected import file; catches `ValidationError`
  per record, formats it via `format_collection_entry_error(label, str(exc))`,
  appends to a `parse_errors` list, and logs the aggregate at INFO:
  `logger.info("collection_import_file_parsed path=%s candidate_count=%d error_count=%d", ...)`.
  `parse_errors` is then joined into the message shown to the user in the import
  dialog (`pypost/ui/presenters/collection_import_actions.py`), so a malformed
  `default` value in an imported file is surfaced to the user as a readable
  per-entry error, not a silent failure or a raw traceback.

In both cases `str(exc)` (Pydantic's `ValidationError.__str__`) already includes
our custom message (`"default value ... is not valid for param type ..."`),
so no additional context needs to be added at the raise site.

**In-app construction is not at risk in practice.** `McpParamsTable.get_data()`
(the only place inside `request_editor.py` that constructs a fresh `McpToolParam`
from user-edited table state) always runs the raw Default text through
`_parse_default()` first, which uses `_COERCERS` to produce a value that is
*already* the correct Python type for the selected `param_type` (or `None`).
`_validate_default_type()` can therefore never raise for a value that came out
of `get_data()` — it is defense-in-depth against future callers, not a path
exercised through the UI today.

**Conclusion for path (1): no logging code change was needed.** The generic
`ValidationError` handling at both data-load boundaries (`storage.py`,
`collection_import.py`) already logs with the right level, the right minimal
context (filename/path + counts, never the raw file content or the full
`Collection`/`RequestData` object), and, for the user-facing import flow,
already surfaces the message through the existing UI dialog. Duplicating a log
call inside `_validate_default_type()` itself would violate this project's
convention (`pypost/models/models.py` and the sibling `Settings.model_validator`
in `pypost/models/settings.py` both raise `ValueError` without logging —
Pydantic models here are raise-only; logging happens at the boundary that
catches `ValidationError`).

### Where path (2) surfaces in production

`_parse_default()` already had a DEBUG-level fallback log (added earlier in
Step 4/this task's development) for the "couldn't coerce this text, dropping
the default" case. It was reviewed for adequacy and its **message was restyled**
to match this project's established structured-logging convention (see below);
level, exception set, and fallback behaviour were left unchanged since they
were already correct.

- **Before**: `logger.debug("Cannot parse %r as %s; ignoring default", stripped, param_type)`
- **After**: `logger.debug("mcp_param_default_coerce_failed value=%r param_type=%s", stripped, param_type)`

Rationale for DEBUG (not WARNING/ERROR): this fires on ordinary, expected user
typing (e.g. switching the Type combo to `integer` while the Default cell still
holds old text, or typing an in-progress value) and is silently recovered by
falling back to no default — directly analogous to the existing DEBUG-level
`variable_name_validation_attempt` log in
`pypost/ui/presenters/env_presenter.py::_is_valid_variable_name()`, which logs
at DEBUG for the same "expected, recoverable, driven by live user input" shape
of event.

### Log Structure

- Structured logs: yes — event-name-first, `key=value`-pairs style
  (`mcp_param_default_coerce_failed value=%r param_type=%s`,
  `storage_collection_load_failed filename=%s error=%s`,
  `collection_import_file_parsed path=%s candidate_count=%d error_count=%d`),
  matching the dominant convention across `pypost/core/` and `pypost/ui/`
  (confirmed by grep: e.g. `template_expression_validation_failed`,
  `secret_backend_chain_resolved_via_fallback`, `variable_set_in_env env_id=%s ...`).
- Includes context: yes — filename/path, param type, coerce-failure counts;
  never the full `Collection`/`RequestData`/table contents.
- Log levels used by this task's paths: DEBUG (`_parse_default` fallback),
  WARNING (`storage.py` load failure, pre-existing), INFO (`collection_import.py`
  aggregate summary, pre-existing).

## Metrics Implementation

Not applicable. No metrics/telemetry infrastructure was added. `McpParamsTable`
is a plain `QTableWidget` with no `self._metrics` dependency injected (unlike,
e.g., `RequestEditorControls` or `EnvPresenter`, which do have a metrics object
and call `self._metrics.track_*` alongside their DEBUG logs). Wiring metrics
into `McpParamsTable` would be new infrastructure for this widget, which is out
of scope per the task instructions — match existing observability patterns
only, do not introduce new ones.

## Monitoring Integration

- [ ] Prometheus metrics — not applicable to this change
- [ ] Grafana dashboards — not applicable to this change
- [ ] Alerting rules — not applicable to this change
- [ ] Log aggregation (ELK, Loki, etc.) — not applicable to this change; project
  uses standard Python `logging` with no aggregation backend configured

## Validation Results

- [x] Logs are correctly formatted (structured `event_name key=value`, matches
  project convention)
- [x] No metrics were added or needed (see above)
- [x] Logging works in error scenarios — verified by re-running the full
  22-test suite covering both the model validator (`test_mcp_tool_contract.py`)
  and the table's parse/coerce/round-trip behaviour
  (`test_request_editor_mcp_params.py`); all 22 pass
- [x] Large data structures are not logged — confirmed by reading every log
  call on both error paths: only filenames, paths, single scalar values,
  param-type strings, and counts are logged, never a full `Collection`,
  `RequestData`, or table dump
- [ ] N/A — no new metrics were introduced, so "metrics available for
  monitoring" does not apply

## Notes

- Code change made in this step: one log-message restyle in
  `pypost/ui/widgets/request_editor.py::McpParamsTable._parse_default()`
  (message text only — event-name + key=value instead of a free-text
  sentence). No change to log level, exception handling, or control flow.
- No changes were made to `pypost/models/models.py`. `McpToolParam` deliberately
  has no logger — it is a Pydantic model that raises `ValueError` on invalid
  input, exactly like `Settings`'s `model_validator` in
  `pypost/models/settings.py`. Callers that construct these models from
  untrusted data are the ones that catch `ValidationError` and log; that
  boundary already exists and already covers the new validator, since Pydantic
  validates nested models transitively.
- Tests: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
  tests/test_mcp_tool_contract.py tests/test_request_editor_mcp_params.py -v`
  — 22 passed, 0 failed, after the log-message edit.
- Lint: `make lint` — clean (flake8 on `pypost/`, markdown lint, relative link
  check).
