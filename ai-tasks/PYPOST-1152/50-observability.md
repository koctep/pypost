# PYPOST-1152: Observability Implementation

## Scope note (read first)

This task is **test-only**: it adds `tests/test_ui_wait_stress.py`, a green forward-looking
regression guard for a PySide6/Qt segfault that could not be reproduced (47/47 clean runs — see
`20-architecture.md`). No production code under `pypost/` was touched, and this test does not
ship as part of any running service. "Observability" here therefore means something narrower
than the template's default framing: *if this guard ever goes red in CI, does the failure output
give whoever investigates next enough forensic signal to act without re-deriving everything from
scratch — and does a passing run leave any trace in a CI log scan at all?* Most of the template's
production-service sections (Prometheus, Grafana, business metrics, resource-usage metrics) do
not apply to a pytest file and are marked N/A below rather than filled with fabricated content.

## Logging Implementation

### Added Logs

The test already had failure-path diagnostics before this step (from Step 4/Development); this
step assessed them and added one line for the passing case.

- **ERR** (`_LOGGER.error(summary)`, pre-existing from Step 4) —
  `test_all_child_runs_exit_zero_under_repeated_isolated_stress`, on any child crash/non-zero
  exit/timeout: logs the full failure summary (count of failed children out of
  `STRESS_ITERATIONS`, per-child `_describe_returncode` signal-name decode, stdout tail (last
  2000 chars) and stderr tail (last 500-1000 chars) per failing child, plus a note that this is
  an unexpected regression, not a pre-excused outcome). The same string is also passed to
  `pytest.fail()`, so it surfaces in the pytest failure report independent of log level/capture
  configuration. `PYTHONFAULTHANDLER=1` is set in every child's environment (pre-existing), so a
  genuine native crash's best-effort Python-side traceback lands in the captured stderr tail this
  message includes.
- **INFO** (`_LOGGER.info(...)`, **added this step**) — same test function, on normal
  (all-children-passed) completion: a single-line summary — `"PYPOST-1152 stress guard passed:
  %d/%d isolated \`pytest %s\` child runs exited 0 in %.1fs"` — logging `STRESS_ITERATIONS` twice
  (as passed/total, currently always equal on this path since any failure short-circuits to the
  ERR branch above), the target module path, and total wall-clock duration via
  `time.monotonic()`. Confirmed with `pytest -v -m slow -s`: renders as `2026-08-30 23:00:20,696
  test_ui_wait_stress INFO PYPOST-1152 stress guard passed: 15/15 isolated \`pytest
  tests/test_ui_wait.py\` child runs exited 0 in 114.2s`.

Rationale for the addition: before this step, a passing run produced zero log output — a CI log
scan (grep over log lines, not `pytest -v` console output) had no way to confirm this guard even
ran, let alone that it passed, without re-running pytest verbosely. The added INFO line closes
that gap cheaply: one line, no per-child data, on the already-hot completion path.

No EMERG/ALERT/CRIT/WARNING/DEBUG lines were added — none are warranted for a single pytest
function with a binary pass/fail outcome and an existing well-formed ERR path. Python's stdlib
`logging` module has no built-in NOTICE level (syslog's NOTICE sits between INFO and WARNING);
rather than register a custom level for one test file, the added summary line uses the nearest
standard stdlib level, INFO, which is proportionate here.

### Log Structure

- Structured logs: No — plain `%s`/`%d`-formatted log messages via stdlib `logging`, consistent
  with the rest of the test suite (no structured/JSON logging convention exists in this
  repository's tests).
- Includes context: Yes on the failure path (child index, signal/exit-code decode, stdout/stderr
  tails); the passing-path line includes iteration counts, target module, and duration, but
  deliberately no per-child data (see "large data structures" rule below).
- Log levels used: `INFO` (new, this step) and `ERROR` (pre-existing, Step 4). Both go through
  the module-level `_LOGGER = logging.getLogger(__name__)` already present in the file.

## Metrics Implementation (if applicable)

N/A. This is a pytest regression-guard test, not a running service or long-lived process — there
is no metrics pipeline, scrape target, or dashboard to instrument. The closest analogue to a
"metric" here is the pass/fail count and wall-clock duration folded into the log line above, which
is sufficient for this artifact's purpose (a CI log scan / test-report consumer, not a
metrics-backed alert).

### Performance Metrics

N/A (see above). Wall-clock duration is captured and logged (see INFO line), which is the
proportionate equivalent for a test rather than a separate metrics emission.

### Business Metrics

N/A — this test has no business-logic surface; it exercises test-infrastructure stability only.

### System Health Metrics

N/A — no resource-usage (CPU/memory/disk) or component-status metrics are emitted or applicable;
each child subprocess is bounded by its own timeout and its exit status is the only "health"
signal this guard is designed to observe.

## Monitoring Integration

- [ ] Prometheus metrics — N/A, not a running service
- [ ] Grafana dashboards — N/A, not a running service
- [ ] Alerting rules — N/A; the alerting mechanism here is CI itself: a red run of this test is a
      CI failure, which is this guard's entire purpose (see module docstring: "a first-class CI
      failure requiring immediate triage")
- [ ] Log aggregation (ELK, Loki, etc.) — N/A / out of scope for this task; whatever log
      aggregation the CI pipeline already applies to pytest/stdlib `logging` output for the rest
      of the suite will pick up the new INFO/ERROR lines with no additional wiring, since this
      test uses the same `logging.getLogger(__name__)` convention as the rest of the codebase.

## Validation Results

- [x] Logs are correctly formatted — verified by running with `-s` (see command below); the INFO
      line rendered with correct interpolation of iteration counts, module path, and duration.
- [x] Metrics are collected correctly — N/A (no separate metrics pipeline); the equivalent
      counts/duration are embedded correctly in the log line, confirmed by the same run.
- [x] Logging works in error scenarios — the ERR path (pre-existing) was exercised and reviewed
      during Step 4 development/code-review; not re-triggered this step (doing so would require
      deliberately breaking `tests/test_ui_wait.py`, which is out of scope), but the code was
      read end-to-end and the message construction/formatting is straightforward string
      interpolation with no changes made to that path this step.
- [x] Large data structures are not logged — confirmed by reading the diff: the new INFO line
      logs only two integers, a module-path string, and a float duration; no stdout/stderr or
      other per-child data is logged on the passing path (that stays failure-only, unchanged from
      Step 4).
- [ ] Metrics are available for monitoring — N/A, no metrics pipeline exists or is warranted for
      this artifact (see Monitoring Integration above).

Test re-run after the logging addition, per this step's instructions:

```
QT_QPA_PLATFORM=offscreen timeout 300 .venv/bin/python -m pytest tests/test_ui_wait_stress.py -v -m slow -s
```

Result: **1 passed in 114.26s**, with the new INFO line visible in the console output:

```
tests/test_ui_wait_stress.py::test_all_child_runs_exit_zero_under_repeated_isolated_stress 2026-08-30 23:00:20,696 test_ui_wait_stress INFO PYPOST-1152 stress guard passed: 15/15 isolated `pytest tests/test_ui_wait.py` child runs exited 0 in 114.2s
PASSED [114.21s]
```

15/15 child runs exited 0, consistent with prior runs recorded in `00-roadmap.md` Step 4 (118.83s
in that run vs. 114.26s here — both well under the 240s per-test timeout / 300s wrapper bound).

## Notes

- This step is intentionally light-touch: the pre-existing failure diagnostics (assertion message
  with per-child stdout/stderr tails, `_describe_returncode` signal-name decoding, and
  `PYTHONFAULTHANDLER=1` in each child's environment for a best-effort native traceback on crash)
  were assessed as already sufficient forensic signal for a red run — see the reasoning captured
  in the module docstring's "Why `PYTHONFAULTHANDLER=1`" section, which predates this step. This
  step's only functional addition is the passing-path INFO summary line, closing the narrower gap
  that a *green* run previously left zero trace in a CI log scan.
- No production code under `pypost/` was touched this step, consistent with the rest of this task
  (see `20-architecture.md` Branch C / no confirmed live defect / no fix warranted).
- Deliberately did not add: a custom NOTICE logging level, structured/JSON logging, metrics
  emission, or any monitoring-system integration — all would be disproportionate engineering for
  a single pytest regression-guard function with a binary outcome, per this step's own scoping
  instruction to keep any addition small and proportionate.
