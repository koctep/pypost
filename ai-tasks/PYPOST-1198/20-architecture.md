# PYPOST-1198: Log worker_timeout on parallel_test_run_started

## Research

- Target code: `scripts/run_parallel_tests.py`, function `run_parallel_tests` (~lines
  531-543). It already logs a single structured INFO line, `parallel_test_run_started`, built
  from a `%s`/`%d`-style format string plus positional args pulled from `config` (a
  `RunnerConfig` instance).
- `RunnerConfig` (same file, ~line 76-87) is a plain `@dataclass` with a `worker_timeout: float`
  field (default `30.0`, set at line 87). The value is already resolved by
  `get_worker_timeout()` (precedence: CLI arg > `WORKER_TIMEOUT` env var > `DEFAULT_WORKER_TIMEOUT`
  = 30.0) before a `RunnerConfig` is constructed, so by the time `run_parallel_tests` runs,
  `config.worker_timeout` already holds the effective bound for this run — no new resolution
  logic is needed here.
- The WARNING-level log that fires when a worker actually exceeds its timeout lives elsewhere in
  the same file and reads `config.worker_timeout` (or an equivalent) at fire time. This task does
  not touch that log statement or its trigger condition, per requirements.
- Existing coverage: `tests/test_run_parallel_tests.py::test_parallel_runner_logs_run_config`
  (~lines 444-468) already asserts, via `caplog`, that the `parallel_test_run_started` message
  contains substrings for `workers=`, `enable_coverage=`, `test_targets=`, and `report_json=`. It
  builds a `RunnerConfig` without passing `worker_timeout` explicitly, so the dataclass default
  (`30.0`) is in effect for that test.
- No external research needed — this is a same-file, same-line, single-field addition to an
  existing structured log call using a pattern (`field=%s` in a `logger.info` format string)
  already used by every other field on this exact line.

## Implementation Plan

1. In `run_parallel_tests` (`scripts/run_parallel_tests.py`, ~lines 531-543), add one more
   `field=%s`-style segment to the existing `parallel_test_run_started` format string (e.g.
   `worker_timeout=%s`) and pass `config.worker_timeout` as the corresponding positional
   argument, following the same ordering/style as the existing `workers`, `enable_coverage`,
   `report_json`, `test_targets`, and `pytest_arg_count` fields.
2. No other production code changes: `RunnerConfig.worker_timeout` already exists and is already
   populated with the effective (override-aware) bound before this log call executes; no new
   computation, config field, CLI flag, or module is introduced.
3. Update `tests/test_run_parallel_tests.py::test_parallel_runner_logs_run_config` to assert the
   new field is present in the logged message.

**Mandatory — Failing Repro (next Step 3):**

- Extend `test_parallel_runner_logs_run_config` in `tests/test_run_parallel_tests.py` (or add a
  small dedicated test alongside it) with a new assertion against the captured
  `parallel_test_run_started` log message, e.g.:
  `assert any("worker_timeout=30.0" in message for message in messages)`
  (the `RunnerConfig` built in that test does not pass `worker_timeout` explicitly, so the
  dataclass default of `30.0` is the expected effective value; the exact string form —
  `worker_timeout=30.0` vs `worker_timeout=30` — should match whatever `%s`-formatting of a
  Python `float` produces, i.e. `30.0`).
- This assertion fails today (red) because `worker_timeout` is not yet part of the
  `parallel_test_run_started` format string or its args — the field simply does not appear in
  the logged message.
- No live external dependencies are involved: the test already runs the real
  `run_parallel_tests(config)` against a local `sample_test_workspace` fixture and captures
  logs via `caplog`, entirely in-process and offline.
- Sequencing: this research/architecture step (Step 2, done) → red test added per above with no
  production code change (Step 3) → independent review of the red test → production fix adding
  the `worker_timeout=%s` field and argument (Step 4) → test goes green.

## Architecture

No architectural change. This is a single-field, additive edit to one existing `logger.info`
call in one function (`run_parallel_tests`) in one file (`scripts/run_parallel_tests.py`). There
are no new modules, layers, interfaces, or data flows:

- **Module involved**: `scripts/run_parallel_tests.py` (existing).
- **Component involved**: `run_parallel_tests()` orchestration function (existing) and
  `RunnerConfig` dataclass (existing, field already present).
- **Change shape**: append `worker_timeout=%s` to the existing format string literal and
  `config.worker_timeout` to the existing positional-args tuple of the one `logger.info(...)`
  call at ~lines 535-543.
- **Pattern**: reuse of the existing structured-logging convention already used by every other
  field on this same log line (`field_name=%s`/`%d` positional formatting) — no new pattern is
  introduced.
- **Interfaces**: none change. `RunnerConfig`'s public shape, `run_parallel_tests`'s signature,
  and the log event's name (`parallel_test_run_started`) are all unchanged; only the message
  body gains one more field.

## Q&A

- **Q: Does this require resolving `worker_timeout` anywhere new?**
  A: No. `config.worker_timeout` is already the resolved, effective value by the time
  `run_parallel_tests` runs (set via `get_worker_timeout()` precedence logic before
  `RunnerConfig` construction, per the ground truth in the task and `10-requirements.md`). This
  task only makes an already-available value visible in the existing log line.
- **Q: Any risk to the WARNING-level timeout log or timeout enforcement behavior?**
  A: No. Neither is touched; scope is strictly the `parallel_test_run_started` INFO line's
  format string and arguments.
