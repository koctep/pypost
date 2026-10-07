# PYPOST-1287: Observability Implementation

## Summary

No production logging or metrics were added. This task changed only test code
(`tests/test_pypost_1077_verification_artifacts.py`, `tests/test_pypost_1287_failing_repro.py`),
one audit report (`ai-tasks/PYPOST-374/30-dialogs-audit-report.md`) and one dev doc
(`doc/dev/verification_artifact_contracts.md`). `git diff --stat -- pypost scripts` is empty, so
no runtime code path was added or changed and none needs monitoring.

The diagnostic surface for this change is the failure output of the validator
`_dialog_audit_report_errors(report_markdown, modules)`. The live test
`test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` joins its errors one per
line in the `assert not errors, "\n".join(errors)` message, which `make test` prints. That
contract is documented below. It is also the refresh oracle for the audit report.

## Logging Implementation

### Added Logs

None. No runtime code changed, so no level applies:

- **EMERG / ALERT / CRIT**: N/A. No runtime component was added or changed.
- **ERR**: N/A. Contract violations are reported as test assertion failures, not logs.
- **WARNING / NOTICE / INFO**: N/A. The validator is a pure function that `pytest` runs. Logging
  in it would duplicate the assertion message and add noise to `make test` output.
- **DEBUG**: N/A. The per-case messages already name the module and both values, so no extra
  trace is needed to find a drift.

### Diagnostic Surface: Failure-Message Contract

Each violation produces one message on its own line. Drift messages (`!=`) print the recorded or
declared value and the discovered value as plain ints with no thousands separators. The
`unparseable` and `invalid LOC` messages print only the raw cell or token as a Python `repr`
(`'<raw>'`), since no positive int could be parsed. The repro regexes depend on these shapes.

| Rule | Condition | Message shape |
| ---- | --------- | ------------- |
| R1 | Section absent (one per name) | `audit report missing section: <name>` |
| R2 | Empty inventory table (1) | `module inventory table must not be empty` |
| R2 | No Module/LOC col (1) | `module inventory table must contain 'Module' and 'LOC' columns` |
| R2 | Discovered, not in inventory | `module inventory missing discovered dialog module: <file>` |
| R2 | Inventory module not discovered | `module inventory lists unknown dialog module: <file>` |
| R2 | Inventory row duplicated | `module inventory lists <file> more than once` |
| R3 | LOC cell not an int, or int `<= 0` | `invalid LOC in inventory for <file>: '<raw>'` |
| R3 | Per-module LOC drift | `<file>: recorded LOC <r> != discovered LOC <d>` |
| R4 | Row sum drift (invalid rows add 0) | `inventory row sum: <sum> != discovered <total>` |
| R4 | Scope / Total statement absent | `audit report missing <label> statement` |
| R4 | Scope / Total LOC token not an int | `<label> unparseable: '<raw>'` |
| R4 | Scope / Total LOC drift | `<label>: declared <x> != discovered <total>` |
| R5 | Verdict phrase absent (3) | `verdict must state completion for all <n> modules` |
| R5 | Scope / Verdict count not a word or int | `<label> unparseable: '<raw>'` |
| R5 | Scope / Verdict count drift | `<label>: declared <x> != discovered <n>` |
| R6 | No testability row | `testability table missing dialog module: <file>` |
| R6 | Testability row not discovered | `testability table lists unknown dialog module: <file>` |
| R7 | Phrase 1 (2) | `executive summary must describe exactly three MCP dialogs` |
| R7 | Phrase 2 (2) | `executive summary must limit the read-only claim to activity and tools` |
| R7 | Phrase 3 (2) | `executive summary must state the server manager mutation capability` |
| R7 | Any `_STALE_CLAIMS` entry present | `report retains contradictory stale claim: <claim>` |

Notes on the table:

- (1) Early return: no other R2/R3/R4-row-sum message is emitted for the inventory.
- R1 `<name>`: `module inventory`, `testability summary`, `executive summary`, `verdict`.
- R4 `<label>`: `scope total LOC` (Scope line) or `Total line LOC` (Total line). The missing
  statement message uses the same labels.
- R5 `<label>`: `scope module count` or `verdict module count`. A missing Scope line is reported
  only by R4; a missing Verdict phrase only by the `verdict must state ...` message.
- (2) R7: the three rows are the `_SEMANTIC_PHRASES` entries, in order. A message is emitted
  when its phrase is absent from the normalized Executive Summary and the whole report:
  phrase 1 `Three MCP dialogs`, phrase 2 `The activity and tools dialogs are read-only`,
  phrase 3 `server manager supports configuration and lifecycle changes`.
- (3) Emitted only when the Verdict section exists; a missing section is reported by R1.

Errors from `check_audit_report_covers` (PYPOST-1259 helper, unchanged) come first in the same
joined message.

### Log Structure

- Structured logs: no. These are plain-text assertion lines, one violation per line.
- Includes context: yes. Most lines name the module, label or claim. Drift lines add the recorded
  and discovered values; `unparseable` and `invalid LOC` lines add the raw token. Exceptions that
  name none: the two R2 early-return messages (empty table, missing columns), the R4
  `inventory row sum` line, the three R7 executive-summary messages and the R5
  `verdict must state completion ...` message.
- Log levels: N/A. This is test output, not runtime logging.
- Large data structures: not printed. Messages hold only names, ints and single raw cells (the
  `unparseable` and `invalid LOC` tokens), never the report body or the full module list.

## Metrics Implementation (if applicable)

### Performance Metrics

N/A. No runtime path changed. The test reads one Markdown file and walks the dialog package. It
is a fast, offline unit test, so no metric is warranted.

### Business Metrics

N/A. The change has no user-facing or request-processing behaviour.

### System Health Metrics

N/A. No resource-consuming or long-lived component was added.

## Monitoring Integration

N/A for every item. The project's OTel integration covers runtime code under `pypost/`, which
this task does not touch. CI visibility comes from `make test` / `make check` failure output.

- [ ] Prometheus metrics: N/A, no runtime code changed
- [ ] Grafana dashboards: N/A, no runtime code changed
- [ ] Alerting rules: N/A. A red `make check` is the alert.
- [ ] Log aggregation (ELK, Loki, etc.): N/A, no runtime logs added

## Validation Results

- [x] Messages are correctly formatted. STEP 3 / STEP 4 repro cases 1-5 assert the per-line shapes
  (module name with recorded and discovered values on one line; `declared X ... discovered Y`).
- [x] Metrics are collected correctly: N/A, no metrics added.
- [x] Diagnostics work in error scenarios. Repro cases 2-5 drive missing, unknown, per-module
  drift, aggregate drift and live drift, and each produces the expected named message.
- [x] Large data structures are not logged. Messages carry names, ints and single raw cells
  only.
- [x] Metrics are available for monitoring: N/A, no metrics added.

## Notes

- No logging was added to test or production code. The step skill targets production
  observability, and this task has no production change.
- The failure output is the operator workflow. When dialog LOC drifts, `make test` lists every
  stale row and aggregate with both values, and the report can be hand-refreshed from that output
  (see `doc/dev/verification_artifact_contracts.md`).
