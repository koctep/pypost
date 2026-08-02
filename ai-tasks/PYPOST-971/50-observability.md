# PYPOST-971: Observability Implementation

## Observability Decision

PYPOST-971 consolidates DisplayRole exact-match ownership into
`pypost.agent.tree_index` (`display_role_equals`,
`find_child_index_by_display_text`). It does not add a new selection
capability, public API, or diagnostic path.

**Decision:** add no production logs or metrics. Retain the existing
scalar-only DEBUG `ui_action_applied` event on successful `ui_select`.
Do not log option text, DisplayRole values, model indexes, or row
payloads from the new helpers (NFR-5, NFR-6, AC-7).

New helper-level logging would either duplicate the existing success
event or expand captured model data beyond the established comparison
and error behavior — both forbidden by requirements.

## Logging Implementation

### Added Logs

None. No logger call, log level, event name, or field set changed.

| Level   | Location | Status                                      |
| ------- | -------- | ------------------------------------------- |
| EMERG   | —        | Not applicable                              |
| ALERT   | —        | Not applicable                              |
| CRIT    | —        | Not applicable                              |
| ERR     | —        | Not applicable (errors remain exceptions)   |
| WARNING | —        | Not applicable                              |
| NOTICE  | —        | Not applicable                              |
| INFO    | —        | Not applicable                              |
| DEBUG   | —        | No new DEBUG lines; existing event retained |

### Existing Logs Preserved

| Event              | Level | Fields                                              | Emitter            |
| ------------------ | ----- | --------------------------------------------------- | ------------------ |
| `ui_action_applied` | DEBUG | `primitive=select`, `widget_id`, `outcome=ok`, `duration_ms` | `ui_select` in `ui_actions.py` |

Emission remains after successful combo / list / tree / item-view
selection and `_pump()`, unchanged by the ownership move:

```text
ui_action_applied primitive=select widget_id=%s outcome=ok duration_ms=%s
```

- Option text is **not** a log field.
- Model DisplayRole strings are compared in-memory only; they are not
  written to logs by `display_role_equals` or
  `find_child_index_by_display_text`.
- `pypost.agent.tree_index` has no logger and gains none in this task.
- Miss / missing-model paths continue to raise
  `UiTargetNotInteractableError` (or e2e `AssertionError`) without a
  new failure log line.

### Log Structure

- Structured logs: yes (space-separated `key=value` DEBUG event prefix).
- Includes context: yes (`primitive`, `widget_id`, `outcome`,
  `duration_ms`).
- Log levels used by this path: DEBUG only.
- Large structures / option payloads: not logged.

## Metrics Implementation

### Performance Metrics

None added. Flat scan remains O(root rows); tree lookup remains the
existing DFS shape (NFR-3). No new timing series beyond the existing
`duration_ms` scalar on `ui_action_applied`.

### Business Metrics

None. Ownership consolidation is not a product conversion or request
count outcome.

### System Health Metrics

None. No resource, process, or component-health behavior changed.

### No-New-Metrics Rationale

- Behavior-preserving refactor; operational surface is unchanged.
- Acceptance is CI green on ownership and selection suites, not a new
  production counter.
- Adding helper-invocation counters would increase cardinality without
  improving incident detection.

## Monitoring Integration

- [ ] New Prometheus metric — not applicable
- [ ] New Grafana dashboard — not applicable
- [ ] New alerting rule — not applicable
- [ ] New log-aggregation field — not applicable
- [x] Existing CI signal via focused selection / ownership tests

## Privacy and Security (NFR-5 / NFR-6)

- Successful select telemetry stays scalar-only.
- Shared match helpers must not emit DisplayRole text, option strings,
  or model dumps.
- Public error messages retain established reasons (`option not found`,
  missing-model, out-of-range); they do not newly serialize full model
  contents.
- Caplog contract for `ui_action_applied` (no secret / fill text in
  logs) remains the privacy baseline for action primitives; select
  must not regress by introducing option payload fields.

## Validation Results

Step 6 validation is by source and requirements review (no new
instrumentation to exercise).

| Check                                                         | Result |
| ------------------------------------------------------------- | ------ |
| `ui_select` still emits scalar-only `ui_action_applied`       | Confirmed in `ui_actions.py` |
| Option / DisplayRole not newly logged                         | Confirmed; helpers have no logger |
| `tree_index` remains log-free                                 | Confirmed by source inspection |
| Architecture: logging / combo / QListWidget / int paths leave | Confirmed against Step 2 plan |
| NFR-5 / AC-7 logging schema unchanged                         | Satisfied by no-new-log decision |
| Existing `test_ui_action_applied_caplog`                      | Unchanged; still covers fill scalar privacy |

Validation checklist from the Step 6 template:

- [x] Logs are correctly formatted (existing event unchanged)
- [x] Metrics are collected correctly (none required / none added)
- [x] Logging works in error scenarios (errors remain exceptions; no new
  failure logs required)
- [x] Large data structures are not logged
- [ ] Metrics are available for monitoring — N/A (no new metrics)

## Troubleshooting

| Symptom                                      | Check |
| -------------------------------------------- | ----- |
| Option text appears in CI / agent logs       | Confirm no logger added to `tree_index`; confirm `ui_select` format still omits option |
| Select success produces no DEBUG event       | Confirm `ui_select` still logs after `_pump()` on the success path |
| Caplog privacy test fails on fill            | Unrelated to this ticket; do not widen select fields to “fix” fill |
| Ownership AST marker fails                   | Shared helpers missing or flat path still inlines DisplayRole |

## Notes

Observability for PYPOST-971 is complete within scope: preserve the
existing scalar `ui_action_applied` success event and do not expand
logged model or option data. Step 6 remains pending review (`[/]`).
