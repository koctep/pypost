# PYPOST-1011: Observability Implementation

## Summary

This is a pure internal refactor: `write_json_export_file` in the new shared
module `pypost/core/export_file_writer.py` was extracted from the two
byte-identical `try/except` write blocks that used to live inline in
`CollectionExportError`'s `write_export_file` and
`EnvironmentExportError`'s `write_export_file`. No caller-visible behavior
changed except the one already covered by Step 3/4: environment export now
also catches `TypeError`/`ValueError` (previously only `OSError`), fixing a
pre-existing gap where a non-serializable environment payload raised a raw
`TypeError` instead of `EnvironmentExportError`.

Conclusion: **no new logging or metrics were added.** Existing logging,
both inside the two domain wrappers and at their call sites, already gives
full coverage of this code path with no loss of context. This finding is
documented below rather than adding speculative logs per the rule file's
guidance.

## Analysis

### What changed structurally

- `pypost/core/export_file_writer.py::write_json_export_file(path, payload, *, error_cls)`
  is the single real implementation (mkdir parents -> `json.dumps` -> write
  UTF-8 text with trailing newline), catching `(OSError, TypeError,
  ValueError)` and re-raising as `error_cls(f"Could not write file: {exc}")`.
  It is intentionally Qt-free and log-free, and does not know which domain
  called it beyond the `error_cls` it's given (see
  `ai-tasks/PYPOST-1011/20-architecture.md`).
- `pypost/core/collection_export.py::write_export_file` and
  `pypost/core/environment_export.py::write_export_file` became thin
  wrappers delegating to the shared helper. Each kept its pre-existing
  `logger.info("<domain>_export_file_written path=%s", path)` line
  unchanged, unconditionally logged after `write_json_export_file` returns
  (i.e. only on success — an exception from the helper propagates before
  this line is reached, so no misleading success log can occur on failure).

### Was the pre-refactor error message/context preserved?

Yes, verified with `git diff HEAD -- pypost/core/collection_export.py
pypost/core/environment_export.py`:

- Collection export: pre-refactor caught exactly
  `(OSError, TypeError, ValueError)` and raised
  `CollectionExportError(f"Could not write file: {exc}") from exc`. The
  shared helper does the identical catch/wrap/message/chain — byte-for-byte
  unchanged behavior.
- Environment export: pre-refactor caught only `OSError` and raised
  `EnvironmentExportError(f"Could not write file: {exc}") from exc`. The
  shared helper now also catches `TypeError`/`ValueError`, so a
  non-serializable environment payload now raises a proper
  `EnvironmentExportError` (message: `"Could not write file: <exc>"`)
  instead of an unhandled `TypeError` escaping to the UI layer. This was the
  intentional, already-reviewed fix that Step 3's red test targeted — it is
  a **strict improvement** in observability/error-surfacing for environment
  export, not a regression, and required no new code in Step 6.
- In both cases `raise ... from exc` preserves exception chaining
  (`__cause__`), so a full traceback including the original `OSError`/
  `TypeError`/`ValueError` is still available to anything that logs
  `exc_info` further up the stack.

### How are errors from `write_export_file` surfaced today?

Checked both UI call sites:

- `pypost/ui/presenters/collection_export_actions.py` (single-collection
  export, lines ~88-94, and bulk export, lines ~124-130): both wrap
  `write_export_file(path, payload)` in `try/except`, log
  `logger.warning("collection_export_failed reason=%s", exc)` /
  `logger.warning("collections_export_failed reason=%s", exc)`, and show the
  error to the user via `show_collection_export_error` /
  `show_all_collections_export_error`. `reason=%s` renders `str(exc)`, i.e.
  the full `"Could not write file: ..."` message from the shared helper —
  no information is lost by the extraction.
- `pypost/ui/widgets/environments/environment_list_widget.py` (export flow,
  lines ~391-398): same pattern —
  `logger.warning("environment_export_failed reason=%s", exc)` then
  `show_export_error(self, str(exc))`.

Both call sites also already log a `logger.info(...)` completion summary
(`collection_export_completed ...`, `collections_export_completed ...`,
`environment_export_completed ...`) with counts and path after a successful
export, in addition to the lower-level `logger.info` inside the domain
`write_export_file` wrappers. This is pre-existing, two-layer success
logging (low-level "file written" + high-level "export completed") that the
refactor does not touch or need to touch.

### Conclusion

No observability gap was introduced by this refactor:

- Success logging: unchanged, still emitted from both domain wrappers
  (`collection_export_file_written path=%s` /
  `environment_export_file_written path=%s`) and from the call sites'
  higher-level completion logs.
- Error logging: unchanged in shape/content. The shared helper raises the
  identical exception type/message contract each domain module always
  raised (`error_cls(f"Could not write file: {exc}")` with `from exc`
  chaining), and both call sites already catch, `logger.warning(...)`, and
  surface these errors to the user.
- The one behavioral difference (environment export now also catching
  `TypeError`/`ValueError`) is a deliberate, already-reviewed fix (Step 3
  red test / Step 4 development) that strictly improves error-surfacing —
  it converts a previously-unhandled crash into a logged, user-facing
  `EnvironmentExportError`, so it needs no additional Step 6 work.

Since existing coverage is sufficient, that finding is documented here
rather than inventing new logs: no logging or metrics were added in this
step. `export_file_writer.py` remains
intentionally log-free and Qt-free, consistent with the Step 4 architecture
decision — adding logging there was considered and rejected because it
would either duplicate the wrappers' existing `logger.info` lines or require
the domain-agnostic helper to infer caller identity beyond what `error_cls`
already conveys.

## Logging Implementation

### Added Logs

No new logs were added. Existing logs already in place (unchanged by this
refactor) are listed for completeness:

- **EMERG**: n/a — not applicable to this code path.
- **ALERT**: n/a — not applicable to this code path.
- **CRIT**: n/a — not applicable to this code path.
- **ERR**: n/a — call sites use `WARNING` (see below), not `ERR`/`ERROR`,
  for export-write failures; this predates the refactor and was not changed.
- **WARNING**: `pypost/ui/presenters/collection_export_actions.py` —
  `collection_export_failed reason=%s` / `collections_export_failed
  reason=%s`; `pypost/ui/widgets/environments/environment_list_widget.py` —
  `environment_export_failed reason=%s`. Logged when `write_export_file`
  raises `CollectionExportError`/`EnvironmentExportError`, immediately
  before surfacing the error to the user via a dialog.
- **NOTICE**: n/a — project does not use a `NOTICE` level; `INFO` is used
  for significant completion events (see below), consistent with existing
  project convention.
- **INFO**: `pypost/core/collection_export.py::write_export_file` —
  `collection_export_file_written path=%s`;
  `pypost/core/environment_export.py::write_export_file` —
  `environment_export_file_written path=%s`. Both logged on successful
  write, after delegating to `write_json_export_file`. Also, at the call
  sites: `collection_export_completed collection_name=%s
  request_count=%d path=%s`, `collections_export_completed
  collection_count=%d request_count=%d path=%s`,
  `environment_export_completed count=%d includes_hidden=%s path=%s`.
- **DEBUG**: n/a — not used in this code path.

### Log Structure

- Structured logs: yes — all log lines use `key=value` tokens in the
  message (e.g. `path=%s`, `reason=%s`, `count=%d`), consistent with the
  rest of the codebase's convention (not a JSON structured-logging
  framework).
- Includes context: yes — success logs include the destination `path`
  (and domain-specific counts); failure logs include `reason` (the
  wrapped exception's message, which itself embeds the original
  `OSError`/`TypeError`/`ValueError` text).
- Log levels used: `INFO` (success/completion), `WARNING` (failure,
  logged by UI call sites before surfacing to the user).

## Metrics Implementation (if applicable)

Not applicable. This is a local file-write helper on the UI/desktop-app
export path with no request/response cycle, no throughput or SLA
requirements, and no existing metrics infrastructure (Prometheus/Grafana)
in this codebase for this kind of operation. No metrics were added,
consistent with "Metrics Implementation (if applicable)" being inapplicable
here.

### Performance Metrics

Not applicable — no performance metrics added or needed for this refactor.

### Business Metrics

Not applicable — no business metrics added or needed for this refactor.

### System Health Metrics

Not applicable — no system health metrics added or needed for this
refactor.

## Monitoring Integration

- [ ] Prometheus metrics — not applicable to this project/feature.
- [ ] Grafana dashboards — not applicable to this project/feature.
- [ ] Alerting rules — not applicable to this project/feature.
- [ ] Log aggregation (ELK, Loki, etc.) — not applicable to this
      project/feature; PyPost is a desktop app using standard Python
      `logging`.

## Validation Results

- [x] Logs are correctly formatted — verified by reading the (unchanged)
      `logger.info`/`logger.warning` call sites; format matches existing
      `key=value` convention used throughout the codebase.
- [x] Metrics are collected correctly — n/a, no metrics in scope.
- [x] Logging works in error scenarios — covered by
      `tests/test_export_file_writer.py::test_write_json_export_file_wraps_os_error_in_error_cls`
      and `test_write_json_export_file_wraps_non_serializable_payload_in_error_cls`,
      plus `tests/test_environment_export.py::test_write_export_file_raises_on_write_failure`,
      `test_write_export_file_raises_on_non_serializable_payload`, and
      `tests/test_collection_export.py::test_write_export_file_raises_on_write_failure`,
      which confirm the correct `error_cls` is raised with the expected
      message on failure (the same exception object the UI layer's
      `logger.warning(reason=%s)` would render).
- [x] Large data structures are not logged — confirmed: no log line in
      `export_file_writer.py`, `collection_export.py`, or
      `environment_export.py` logs the `payload` itself; only path,
      counts, and exception messages are logged.
- [ ] Metrics are available for monitoring — n/a, no metrics in scope.

## Notes

- `pypost/core/export_file_writer.py` was deliberately kept log-free per
  the Step 4 architecture decision (see
  `ai-tasks/PYPOST-1011/20-architecture.md`): it is domain-agnostic and
  does not know which caller (`collection_export` vs `environment_export`)
  invoked it beyond the `error_cls` argument. Adding a log line there would
  either (a) require inventing a synthetic "domain" label not otherwise
  needed by the code, which the architecture explicitly avoided, or
  (b) duplicate the `logger.info(...)` line each wrapper already emits on
  success. Neither is warranted; the existing two-layer logging (helper
  callers' `logger.info` + UI call sites' `logger.warning`/`logger.info`)
  is sufficient and was left untouched.
- Verified via `git diff HEAD -- pypost/core/collection_export.py
  pypost/core/environment_export.py` that the extraction preserved the
  exact `(OSError, TypeError, ValueError)` catch set and
  `f"Could not write file: {exc}"` message format for collection export,
  and intentionally *widened* the catch set for environment export from
  `OSError` alone — the fix that Step 3's red test targeted — with no
  observability regression in either case.
- Full test run: `make test PYTEST_ARGS="tests/test_environment_export.py
  tests/test_collection_export.py tests/test_export_file_writer.py -v"` —
  27/27 passed.
