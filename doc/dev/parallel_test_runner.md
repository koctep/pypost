# Parallel Test Runner Orchestrator (PYPOST-1149 / PYPOST-1192)

## Overview

`make test` and `make test-cov` invoke `scripts/run_parallel_tests.py`, a file-level
orchestrator that runs each `tests/test_*.py` module in its own OS subprocess. A
`ThreadPoolExecutor` schedules up to *N* subprocesses concurrently, where *N* is the effective
worker count.

This design keeps Qt/PySide6 tests isolated: each subprocess gets a fresh `QApplication` and
event loop, with `QT_QPA_PLATFORM=offscreen` set in the child environment. In-process parallel
runners (for example `pytest-xdist` workers sharing one process) are unsuitable for this suite.

Each worker subprocess is bound by a per-file wall-clock timeout (PYPOST-1192). When the bound
expires, the child is killed, the file is recorded as `timed_out`, and the overall run fails
without hanging the pool. See [Worker timeout](#worker-timeout-pypost-1192).

When `scripts/run_parallel_tests.py` is absent, the Makefile falls back to a single
`python -m pytest` invocation (legacy path).

Integration tests for the orchestrator live in `tests/test_run_parallel_tests.py`.

## Architecture

| Component | Role |
| --- | --- |
| `CLIParser` | Parses orchestrator flags (`--workers`, `--worker-timeout`, `--cov`, `--report-json`) and forwards pytest options (`-k`, `-m`, `-v`, `--tb`, `--timeout`, …) to each subprocess |
| `TestDiscovery` | Resolves `test_*.py` files from explicit targets or from `tests/` when no targets are given |
| `SubprocessTestExecutor` | Runs one test file per subprocess with `QT_QPA_PLATFORM=offscreen`, repo-root `PYTHONPATH`, and `subprocess.run(..., timeout=worker_timeout)` |
| `CoverageManager` | Assigns per-worker `COVERAGE_FILE` under `.coverage_parallel/`, then runs `coverage combine`, `coverage report`, and `coverage html` |
| `JsonReporter` | Writes optional machine-readable run summary (`--report-json`) |
| `run_parallel_tests()` | Main entry: discovery → worker pool → failure grouping (including timed-out files) → slowest-files report → optional JSON |

```text
make test / make test-cov
        │
        ▼
scripts/run_parallel_tests.py  (ThreadPoolExecutor)
        │
        ├── subprocess: pytest tests/test_a.py  (timeout=worker_timeout)
        ├── subprocess: pytest tests/test_b.py
        └── subprocess: pytest tests/test_n.py
        │
        ├─ TimeoutExpired → TIMED_OUT + WARNING worker_timeout
        │
        ▼ (when --cov)
.coverage_parallel/.coverage.worker_*  →  coverage combine  →  report + htmlcov/
```

Timeout is enforced **inside** the pool thread via `subprocess.run(..., timeout=...)`, not via
`Future.result(timeout=...)`. A future-only timeout would stop the collector from waiting but
would leave the hung child and pool thread running, so the orchestrator could still stall on
shutdown.

Structured logging (`logger.*` on stderr) complements CLI progress on stdout; see
`ai-tasks/PYPOST-1149/50-observability.md` and `ai-tasks/PYPOST-1192/50-observability.md`.

## Makefile usage

The root `Makefile` defines `WORKERS` and `WORKER_TIMEOUT` with computed / suite defaults:

```makefile
WORKERS ?= $(shell PYTHONPATH=. python3 -c 'from scripts.run_parallel_tests import default_worker_count; print(default_worker_count())')
WORKER_TIMEOUT ?= 120
```

Default worker policy in `default_worker_count()` (PYPOST-1154):

```text
cpu = max(1, os.cpu_count() or 4)
workers = min(cpu + 2, 16)
```

Modest oversubscription for I/O-bound subprocess pytest; cap limits memory from many
concurrent Qt-heavy workers. On a 6-core host the default is eight workers.

| Target | Orchestrator invocation |
| --- | --- |
| `make test` | `scripts/run_parallel_tests.py --workers $(WORKERS) --worker-timeout $(WORKER_TIMEOUT)` + default `-m "not slow"` (unless `PYTEST_ARGS` overrides) |
| `make test-cov` | Same with `--cov` (combines worker coverage after all files finish) |

Examples:

```bash
make test                          # default workers; WORKER_TIMEOUT=120 via Make
make test WORKERS=4                # four concurrent subprocesses
make test WORKER_TIMEOUT=180       # raise per-file wall-clock bound
make test-cov WORKERS=8            # parallel run with combined coverage
make test PYTEST_ARGS='tests/test_foo.py -v'   # single file; PYTEST_ARGS replaces default marker
make test-cov PYTEST_ARGS='-m slow' WORKERS=2  # slow tests only, two workers
```

Other test targets (`test-slow`, `test-agent-e2e`, `test-mcp-collection-e2e`, …) still call
`python -m pytest` directly and are **not** routed through the parallel orchestrator.

## CLI flags

Direct invocation (same binary the Makefile uses):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/run_parallel_tests.py [orchestrator flags] [pytest passthrough] [test paths]
```

### Orchestrator flags

| Flag | Description |
| --- | --- |
| `-n N`, `--workers N`, `--workers=N`, `-nN` | Worker count (positive integer). Highest precedence for concurrency. |
| `--worker-timeout N`, `--worker-timeout=N` | Per-file wall-clock bound in seconds (positive float). Highest precedence for timeout. Distinct from pytest-timeout `--timeout`, which remains passthrough. |
| `--cov` | Enable per-file coverage collection and post-run combine/report (`--cov=pypost`, `htmlcov/`). Also accepts `--cov=package` passthrough into pytest args. |
| `--report-json PATH`, `--report-json=PATH` | Write JSON summary after the run (see schema below). |

### Worker count precedence

1. CLI `--workers` / `-n`
2. Environment variable `WORKERS`
3. Environment variable `PYTEST_WORKERS`
4. `default_worker_count()` — `min(cpu + 2, 16)` where `cpu = max(1, os.cpu_count() or 4)`

### Worker timeout precedence

1. CLI `--worker-timeout` / `--worker-timeout=N`
2. Environment variable `WORKER_TIMEOUT`
3. Script product default `30` seconds (`DEFAULT_WORKER_TIMEOUT`)

Invalid or non-positive CLI/env values are ignored and fall through to the next layer.

### Dual defaults (script vs Make)

| Invocation | Effective default |
| --- | --- |
| `scripts/run_parallel_tests.py` directly (no flag/env) | **30** seconds (product default) |
| `make test` / `make test-cov` | **120** seconds (`WORKER_TIMEOUT ?= 120`, passed as `--worker-timeout`) |

Make uses 120 so legitimate slow suite files (for example makefile smoke modules around 64–87s)
are not false-`TIMED_OUT` under the script's 30s product default. Direct script runs without
Make still use 30 unless overridden.

Do not use bare `--timeout` as an orchestrator flag: pytest-timeout owns that name, and the
parser forwards it into every worker.

### Pytest passthrough

These flags (and their values when required) are forwarded to **every** subprocess:

`-k`, `-m`, `-o`, `-c`, `-W`, `--override-ini`, `--ignore`, `--deselect`, `--tb`, `--capture`,
`--color`, `--maxfail`, `--timeout`, plus other unknown `-` prefixed options.

Positional arguments are test paths (files, directories, or globs). With no positional targets,
discovery scans `tests/test_*.py`.

### JSON report schema (`--report-json`)

```json
{
  "summary": {
    "total_files": 105,
    "passed_files": 104,
    "failed_files": 1,
    "skipped_files": 0,
    "wall_clock_seconds": 8.42,
    "cumulative_duration_seconds": 32.15,
    "workers": 8,
    "status": "failed"
  },
  "slowest_files": [
    { "file": "tests/test_example.py", "duration_seconds": 5.32 }
  ],
  "results": [
    {
      "file": "tests/test_example.py",
      "status": "passed",
      "exit_code": 0,
      "duration_seconds": 0.24,
      "stdout": "...",
      "stderr": ""
    },
    {
      "file": "tests/test_hang.py",
      "status": "timed_out",
      "exit_code": -9,
      "duration_seconds": 30.01,
      "stdout": "",
      "stderr": "worker timed out after 30.0s"
    }
  ]
}
```

Per-file `status` values: `passed`, `failed`, `skipped`, `timed_out`. Timed-out files use
`exit_code: -9` (kill-on-timeout sentinel) and increment `failed_files`; summary `status` is
`failed` when any file failed or timed out (or coverage threshold fails).

Exit codes: `0` when `RunSummary.is_success` (no failed/timed-out files; coverage threshold
failure counts as a failure); `1` otherwise.

## Worker timeout (PYPOST-1192)

### Behavior

For each test file, `SubprocessTestExecutor.run_test_file` calls:

```text
subprocess.run(..., timeout=config.worker_timeout)
```

On `subprocess.TimeoutExpired`:

1. The direct child process is killed (stdlib `subprocess` timeout path).
2. Result status is `TestStatus.TIMED_OUT` (`"timed_out"`).
3. Structured WARNING is emitted: `worker_timeout file=… timeout_seconds=…`.
4. Progress line prints `TIMED_OUT`; the file appears in the FAILURES section with a stderr note
   `worker timed out after Ns`.
5. `failed_files` increments; `is_success` is false; process exit code is `1`.

Ordinary pytest failures remain `failed`; timeouts are distinguishable by status and logs.

Process-group / grandchild teardown is out of scope; if orphans appear after kill, that is
follow-up hardening debt.

### Structured logs (timeout path)

| Level | Event | Fields |
| --- | --- | --- |
| WARNING | `worker_timeout` | `file`, `timeout_seconds` (primary operator signal at kill time) |
| INFO | `test_file_completed` | `status=timed_out`, plus usual completion fields |
| ERROR | `test_file_timed_out` | `file`, `exit_code`, `duration_seconds` (FAILURES pass; distinct from `test_file_failed`) |

Example:

```text
WARNING worker_timeout file=tests/test_hang.py timeout_seconds=30.0
```

`parallel_test_run_started` does not currently include `worker_timeout=…`; operators read the
bound from CLI/Make/env or from a timeout WARNING.

## Subprocess isolation and Qt offscreen

Each test file runs as:

```text
python -c "import sys, os, pytest; code = int(pytest.main(sys.argv[1:])); ...; os._exit(code)" <test_file> [pytest args]
```

Environment setup per subprocess:

| Variable | Value |
| --- | --- |
| `QT_QPA_PLATFORM` | `offscreen` (forced in child; Makefile also sets it on the orchestrator process) |
| `PYTHONPATH` | Repository root prepended to any existing `PYTHONPATH` |
| `COVERAGE_FILE` | Unique path under `.coverage_parallel/` when `--cov` is active |

Using `os._exit()` in the child avoids pytest/Qt shutdown races. When a subprocess exits, the OS
reclaims all Qt state — no shared `QApplication` between test modules.

Pytest exit code **5** (no tests collected, for example after `-k` / `-m` filters) is classified
as **skipped** at the file level, not failed.

## Console output

During the run, each completed file prints one progress line:

```text
[  1/105] tests/test_about_dialog.py ... PASSED (0.24s)
[  2/105] tests/test_hang.py ... TIMED_OUT (30.01s)
```

After completion:

- Grouped **FAILURES** section with stdout/stderr per failed or timed-out file
- **TOP 5 SLOWEST FILES** ranking (timed-out files may appear by duration)
- **SUMMARY** with wall-clock time, cumulative subprocess time, and speedup ratio

## Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Qt singleton / event-loop errors when raising `WORKERS` | Tests running in-process instead of via orchestrator | Use `make test`, not bare `pytest tests/` on the full suite; confirm `scripts/run_parallel_tests.py` exists |
| Segfault or EGL errors on Linux CI | Missing Qt runtime libraries on runner | CI installs packages via `.github/actions/install-qt-egl-runtime`; see [testing.md § Local vs CI parity](testing.md#local-vs-ci-test-parity-troubleshooting-pypost-723) |
| All files show SKIPPED, exit 0 | `-k` / `-m` filter matched no tests in some files | Expected (exit code 5 → skipped); tighten or change `PYTEST_ARGS` |
| `make test` ignores `WORKERS` | Override ignored or invalid env | Default is computed at Make parse time; pass `WORKERS=4` to override |
| File shows `TIMED_OUT` under direct script run | Script default is 30s; file wall clock exceeded it | Use `make test` (120s) or raise bound: `--worker-timeout 120` / `WORKER_TIMEOUT=120` |
| File shows `TIMED_OUT` under `make test` | File exceeded `WORKER_TIMEOUT` (default 120) | Raise `WORKER_TIMEOUT=180 make test` (or CLI equivalent); investigate hangs separately |
| Coverage below 70% fails run | Combined report enforces `--cov-fail-under` (default 70 from `pyproject.toml`) | Run `make test-cov`, inspect terminal report; override with `PYTEST_ARGS='--cov-fail-under=0'` only when debugging |
| Stale `.coverage` or missing combine | Interrupted prior run | Re-run `make test-cov`; orchestrator clears `.coverage_parallel/` and root `.coverage` on start |
| Single file debug | Full suite parallelism obscures failure | `make test PYTEST_ARGS='tests/test_foo.py -vv --tb=long'` (one subprocess) |
| Orchestrator missing | Script deleted or wrong cwd | Makefile falls back to single-process pytest; restore script for parallel/Qt isolation |
| JSON report huge | Per-file stdout/stderr embedded | By design for CI artifacts; omit `--report-json` for local runs |

Focused orchestrator tests:

```bash
make test PYTEST_ARGS='tests/test_run_parallel_tests.py -v'
```

Direct script with JSON export:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/run_parallel_tests.py \
  --workers 2 --worker-timeout 120 --report-json /tmp/pypost-test-report.json -m "not slow"
```

## References

- [Testing via MCP and Prometheus](testing.md) — primary pytest/Makefile reference
- [GUI Testing](gui_testing.md) — Qt offscreen patterns and `qapp` fixture
- `ai-tasks/PYPOST-1149/20-architecture.md` — design rationale and diagrams
- `ai-tasks/PYPOST-1149/50-observability.md` — structured logging fields (base orchestrator)
- `ai-tasks/PYPOST-1192/20-architecture.md` — worker timeout design
- `ai-tasks/PYPOST-1192/50-observability.md` — timeout log events (`worker_timeout`, `test_file_timed_out`)
