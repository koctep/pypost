# PYPOST-1003: Observability Implementation

## Summary

This is a pure data-shape/reporting-accuracy fix: `CollectionImportPlanResult.renamed`
and `ImportPlanResult.renamed` changed from `dict[str, str]` to `list[tuple[str, str]]`
so every rename pair is preserved instead of same-named duplicates overwriting each
other. No new operation, code path, error condition, or externally-visible behavior
was introduced — only the count reported for existing rename events is corrected.
**No new logging or metrics were added**, because the existing logging at both
consumer call sites already reports the corrected count automatically, verified below.

## Verification of Existing Logging

### `pypost/ui/presenters/collection_import_actions.py` (import_collections, line ~87-96)

```python
logger.info(
    "collection_import_completed added_count=%d updated_count=%d "
    "skipped_count=%d renamed_count=%d request_count=%d error_count=%d",
    len(result.added),
    len(result.updated),
    len(result.skipped),
    len(result.renamed),
    result.request_count,
    len(result.parse_errors),
)
```

`renamed_count=%d` is `len(result.renamed)`. Before the fix, `result.renamed` was a
`dict[str, str]` keyed by original name, so 3 same-named duplicates collapsed to 1
dict entry and `len()` undercounted (reported 1 instead of 2 rename events). After the
fix, `result.renamed` is `list[tuple[str, str]]` with one tuple per rename event, so
`len()` on the same expression now returns the correct count with **zero code change**
to this call site.

`success = bool(result.added or result.updated or result.renamed)` (line 97) — a
non-empty `list` and a non-empty `dict` are both truthy, so this boolean logic is
unaffected by the type change.

### `pypost/ui/widgets/environments/environment_list_widget.py` (import handler, line ~328-338)

```python
logger.info(
    "environment_import_completed added_count=%d updated_count=%d "
    "skipped_count=%d renamed_count=%d error_count=%d",
    len(result.added),
    len(result.updated),
    len(result.skipped),
    len(result.renamed),
    len(result.parse_errors),
)
```

Same pattern and same conclusion: `len(result.renamed)` on the new
`list[tuple[str, str]]` now correctly reflects the number of rename events, with no
code change required here either. `success = bool(result.added or result.updated or
result.renamed)` (line 338) is likewise unaffected by the truthiness of list vs. dict.

### Other consumers checked

`grep -rn "plan_collection_import\|plan_import\|format_collection_import_result\|
format_import_result\|\.renamed" pypost --include="*.py"` confirms the only two
consumers of `.renamed` (and of `plan_collection_import`/`plan_import`/
`format_collection_import_result`/`format_import_result`) outside
`pypost/core/collection_import.py` and `pypost/core/environment_import.py` are the two
UI call sites above. There are no other logging or metrics sites touching `.renamed`.

### Unrelated existing `logger.info` calls in the touched core modules

Both `pypost/core/collection_import.py` (line 146, inside the file-reading helper) and
`pypost/core/environment_import.py` (line 92, inside its file-reading helper) contain a
`logger.info("..._file_parsed path=%s candidate_count=%d error_count=%d", ...)` call.
These log parse-time candidate/error counts before any rename planning happens and do
not reference `.renamed` at all — they are unaffected by this fix and required no
review beyond confirming they are out of scope.

`plan_collection_import` and `plan_import` themselves (the functions that build the
`renamed` list) contain no logging of their own; all `renamed`-count logging happens at
the two UI call sites documented above, which is where structured operator-facing logs
for this workflow belong (per existing codebase convention — the plan functions are
pure and side-effect-free).

## Logging Implementation

### Added Logs

None. No new logging was added — the existing `renamed_count=%d` INFO logs at both UI
call sites already report the corrected value automatically once the `renamed` field's
underlying type changed, since `len()` behaves identically on the count-of-events
semantics for both `list[tuple[str,str]]` and the old `dict[str,str]`.

### Log Structure

Log format used (pre-existing, unchanged by this task):
- Structured logs: yes (key=value pairs via `%s`/`%d` format specifiers)
- Includes context: yes (added/updated/skipped/renamed counts, request/error counts)
- Log levels: INFO (`collection_import_completed`, `environment_import_completed`,
  `collection_import_file_parsed`, `environment_import_file_parsed`)

## Metrics Implementation (if applicable)

Not applicable. This fix does not introduce a new operation, throughput concern, or
business/system-health metric — it corrects the count reported by an existing INFO log
line. No Prometheus/Grafana metrics exist for this workflow today and none were added,
consistent with the Definition of Done's explicit scope boundary (reporting-accuracy
fix only, no new functionality).

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable, none exist for this workflow
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [ ] Log aggregation (ELK, Loki, etc.) — no change; existing `logging` module output
  flows through whatever aggregation is already configured for the app

## Validation Results

- [x] Logs are correctly formatted — verified by reading the two call sites; format
  strings and argument order unchanged, only the runtime value of `len(result.renamed)`
  is now accurate
- [x] Metrics are collected correctly — N/A, no metrics for this workflow
- [x] Logging works in error scenarios — no new error path was introduced by this fix;
  existing `parse_errors`/`error_count` logging untouched
- [x] Large data structures are not logged — `result.renamed` itself (the list of
  rename tuples) is never logged directly at either call site, only its `len()`; this
  was true before the fix (only `len()` of the dict was logged) and remains true after
- [x] Metrics are available for monitoring — N/A

Confirmed via `grep -rn` that `pypost/ui/presenters/collection_import_actions.py` and
`pypost/ui/widgets/environments/environment_list_widget.py` are the only two consumers
of `.renamed` besides the two core modules, and both were already reviewed and require
no change (also documented in Step 4's roadmap notes). Re-ran
`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_collection_import.py
tests/test_environment_import.py -q` as a baseline check: 38 passed, confirming no
regression from this observability review (no code was changed in this step).

## Notes

This step required no code changes. The task's Definition of Done explicitly scopes
this as a reporting/data-shape correction with no new functionality, error paths, or
externally-visible behavior beyond the corrected count — and that is exactly what was
found: the pre-existing `renamed_count=%d` INFO logs at both UI call sites already
benefit from the fix automatically because `len()` has identical count-of-events
semantics on `list[tuple[str, str]]` as it did (incorrectly, due to key-collapsing) on
`dict[str, str]`. Inventing new logging or metrics here would not serve any real
observability gap and was avoided per the task's explicit guidance not to add
unnecessary logging just to fill the template.
