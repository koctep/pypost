# PYPOST-1040: Observability Implementation

## Scope Note (read first)

PYPOST-1040 is a diagnostic ticket. Per `ai-tasks/PYPOST-1040/10-requirements.md`'s "What is
out of scope" section, no production application behavior may be changed unless a concrete,
evidenced PyPost-owned defect were found — and Step 2's ablation (see
`ai-tasks/PYPOST-1040/20-architecture.md`) traced the crash to an **upstream PySide6/shiboken6
6.11.1 defect**, not a PyPost-owned one. Consequently **no file under `pypost/` was touched by
this task at any step**, and this step's usual purpose (add production logging/metrics for a
newly implemented feature or fix) does not apply here — there is no new production code path to
instrument.

The only artifact this task produced is `tests/test_agent_dialog_settle_teardown_stress.py`, a
subprocess-based stress detector (already through Steps 3-5: red repro, `xfail(strict=False)`
marking, and a clean-lint pass). This step's applicable scope was therefore narrowed to one
question: **is that test's own failure-diagnostic output adequate for someone triaging it
later, or is something missing?** The sections below are filled out honestly against that
narrower scope; template sections that presuppose production logging/metrics are marked N/A
rather than deleted, per this step's instructions.

## Logging Implementation

### Added Logs

This is a test artifact, not a production code path, so the syslog-severity taxonomy below is
mapped to test-diagnostic intent rather than to production system states:

- **EMERG**: N/A — no production code touched.
- **ALERT**: N/A — no production code touched.
- **CRIT**: N/A — no production code touched.
- **ERR**: N/A — the existing `pytest.fail(summary)` call already serves as the test's "this
  attempt failed" signal (pytest's own FAILED/XFAILED bookkeeping), so a duplicate `ERROR`-level
  log was not added on top of it.
- **WARNING**: `tests/test_agent_dialog_settle_teardown_stress.py`,
  `test_all_child_runs_exit_zero_under_repeated_teardown_stress`, immediately before the
  existing `pytest.fail(summary)` call (in the `if failures:` block) — `_LOGGER.warning(summary)`
  logs the same per-child crash evidence (return code / signal name via `_describe_returncode`,
  and stdout/stderr tails) that is passed to `pytest.fail`. This is the one change this step
  made; see "Why this was added" below.
- **NOTICE**: N/A — not used by this test file.
- **INFO**: N/A — not used by this test file.
- **DEBUG**: N/A — not used by this test file (the *target* module,
  `tests/test_agent_dialog_settle_e2e.py`, has its own DEBUG-log assertions from
  PYPOST-934/PYPOST-968, but that module was explicitly out of scope for edits per
  `10-requirements.md`, and this test only spawns it as a subprocess — it does not capture or
  re-emit the child's own log records, only its stdout/stderr/exit status).

### Why this was added

Before this step, the test already built a detailed diagnostic message per failing child
(`_describe_returncode` naming the signal, plus 2000/1000-char stdout/stderr tails) and passed
it to `pytest.fail(summary)`. On inspection (reading pytest 8.4.2's `_pytest/skipping.py` and
`_pytest/terminal.py` installed in this repo's `.venv`), that detail turns out to be **invisible
by default** when the test's expected outcome fires:

- The test is `xfail(strict=False)`. When a child crash triggers the `pytest.fail()` call,
  pytest's `pytest_runtest_makereport` hook (`_pytest/skipping.py`) reclassifies the report's
  `outcome` from `"failed"` to `"skipped"` (with `rep.wasxfail` set to the *static*
  `xfail(reason=...)` string) rather than clearing `rep.longrepr`.
  `_pytest/terminal.py`'s `summary_xfailures()` only prints that longrepr (i.e. the *dynamic*
  `pytest.fail()` message, with the actual per-child evidence) when `--xfail-tb` is passed; its
  default is `False` (`_pytest/terminal.py` `pytest_addoption`), and this repo's
  `pyproject.toml`, `Makefile`, and `.github/workflows/test.yml` never set it.
- The verbose per-test line (`-v`, which this repo's `pyproject.toml` `addopts` does enable) and
  the `-r`/short-summary line both only ever print `rep.wasxfail` — the static marker reason —
  never the dynamic message.
- Net effect: on the expected "crash reproduced" path, a future triager running
  `make test-slow` (this repo's only invocation path for `slow`-marked tests; this test is
  excluded from the main CI job by `-m "not slow"`) would see only the generic static reason
  ("PYPOST-1040: intermittent upstream PySide6/shiboken6 ... crash") and **none** of the
  specific per-child evidence (which child, which signal, what its output tail said) — despite
  that evidence already being fully assembled in code.

This is a genuine, narrow diagnostic gap in the artifact's own reporting, not a gap in the
detection logic itself (the detection — spawning children, checking exit codes — was correct
and unchanged). The fix: log the same `summary` string at `WARNING` via a module-level
`logging.getLogger(__name__)` right before the existing `pytest.fail(summary)` call. This
repo's `pyproject.toml` sets `log_cli = true` / `log_cli_level = "WARNING"`, and
`.github/workflows/test.yml`'s main job additionally sets `--log-file=pytest.log
--log-file-level=WARNING`; both mechanisms stream log records live as they are emitted, gated
only by level, independent of pytest's later `outcome`/`wasxfail` report reclassification. So
the `WARNING` log is visible under `make test-slow` (which does not override `log_cli`)
regardless of whether pytest ultimately reports the test as `XFAIL`, `FAILED`, or (after an
upstream fix) `XPASS`.

No other line in the test was touched: `STRESS_ITERATIONS`, `CHILD_TIMEOUT_S`,
`_run_child`, `_describe_returncode`, the per-child loop, and the `pytest.fail(summary)` call
itself are all unchanged. No new dependency was added (`logging` is stdlib).

### Log Structure

- Structured logs: No — this is a single free-text `WARNING` message (the same `summary` string
  already built for `pytest.fail`), not a structured/JSON log line. A test-diagnostic artifact
  does not carry the same structured-logging contract as production code (see PYPOST-968's
  logging-contract scope, which this task is explicitly not part of).
- Includes context: Yes — the message embeds the per-child index, return-code/signal name
  (`_describe_returncode`), and stdout/stderr tails for every failing child, plus a pointer to
  `ai-tasks/PYPOST-1040/20-architecture.md` for full background.
- Log levels used: `WARNING` only (one new call site).

## Metrics Implementation (if applicable)

N/A. No production code was touched, and no metrics pipeline (counters, gauges, timers) exists
or was warranted for a single xfail-marked stress test. Adding metrics instrumentation to a
test-only artifact just to fill this template section would be manufactured work with no
consumer — the sub-sections below are marked N/A rather than invented.

### Performance Metrics

N/A — see above. (The test does record wall-clock behavior implicitly via pytest's own
`--durations` reporting when requested, and via the module-level `pytest.mark.timeout(150)`
guard already present before this step; no new performance metric was added.)

### Business Metrics

N/A — this is a diagnostic test artifact, not a business code path.

### System Health Metrics

N/A — no production component was instrumented.

## Monitoring Integration

- [ ] Prometheus metrics — N/A, no production code touched.
- [ ] Grafana dashboards — N/A, no production code touched.
- [ ] Alerting rules — N/A, no production code touched.
- [ ] Log aggregation (ELK, Loki, etc.) — N/A beyond this repo's existing `pytest.log` file
  (`--log-file`, main CI job) and `log_cli` console stream (both pre-existing repo conventions,
  not introduced by this task); no new aggregation target was added or required.

## Validation Results

- [x] Logs are correctly formatted — the new `_LOGGER.warning(summary)` call reuses the exact
  same `summary` string already built (and already validated in Step 3/4) for
  `pytest.fail(summary)`; `%(asctime)s %(levelname)-8s %(name)s: %(message)s`
  (`pyproject.toml log_format`) applies to it like any other log record in this repo.
- [x] Metrics are collected correctly — N/A, no metrics added.
- [x] Logging works in error scenarios — verified by static/source-level analysis of pytest
  8.4.2's `_pytest/skipping.py` (`pytest_runtest_makereport`) and `_pytest/terminal.py`
  (`summary_xfailures`, `short_test_summary`, `pytest_runtest_logreport`) installed in this
  repo's `.venv`, confirming the `log_cli`/`--log-file` handlers attach independently of the
  xfail/fail report-outcome reclassification described above. A full live `STRESS_ITERATIONS =
  25` run was **not** executed to trigger a real crash for this step (multi-minute,
  probabilistic, and Step 4 already documented that a full stress run is not needed to validate
  wiring changes of this kind) — `python -m py_compile`, `flake8`, and
  `pytest tests/test_agent_dialog_settle_teardown_stress.py --collect-only -m slow -q` were run
  instead and all pass cleanly.
- [x] Large data structures are not logged — the `WARNING` message reuses the existing
  `pytest.fail` summary, which already truncates each child's stdout/stderr to fixed tails
  (2000/1000 chars) rather than logging unbounded output.
- [ ] Metrics are available for monitoring — N/A, no metrics added.

## Notes

- This step made exactly one code change, confined to
  `tests/test_agent_dialog_settle_teardown_stress.py`: added `import logging`, a module-level
  `_LOGGER = logging.getLogger(__name__)`, and one `_LOGGER.warning(summary)` call immediately
  before the pre-existing `pytest.fail(summary)`. No other file, and no line of
  `pypost/`, was touched.
- The improvement is deliberately narrow: it does not change what is detected (subprocess
  spawning, exit-code/signal checking), how many iterations run (`STRESS_ITERATIONS = 25`,
  unchanged), or the `xfail(strict=False)` marking decision made in Step 4 — it only ensures the
  diagnostic detail the test already computes is not silently dropped by pytest's default
  xfail-report formatting when that expected outcome fires.
- If a future engineer wants the full per-child detail surfaced in the main CI job's own log
  file even though this test does not currently run there (`-m "not slow"` excludes it), that
  would require enabling the `slow` marker for this test in a CI job and/or passing
  `--xfail-tb` — both are CI-configuration changes outside this test file, and outside this
  step's scope (`.github/workflows/test.yml`, `pyproject.toml`, and `Makefile` were not
  touched).
