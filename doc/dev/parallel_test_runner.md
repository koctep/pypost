# Parallel Test Runner Orchestrator (PYPOST-1149)

## Overview

`make test` and `make test-cov` invoke `scripts/run_parallel_tests.py`, a file-level
orchestrator that runs each `tests/test_*.py` module in its own OS subprocess. A
`ThreadPoolExecutor` schedules up to *N* subprocesses concurrently, where *N* is the effective
worker count.

This design keeps Qt/PySide6 tests isolated: each subprocess gets a fresh `QApplication` and
event loop, with `QT_QPA_PLATFORM=offscreen` set in the child environment. In-process parallel
runners (for example `pytest-xdist` workers sharing one process) are unsuitable for this suite.

When `scripts/run_parallel_tests.py` is absent, the Makefile falls back to a single
`python -m pytest` invocation (legacy path).

Integration tests for the orchestrator live in `tests/test_run_parallel_tests.py`.

## Architecture

| Component | Role |
| --- | --- |
| `CLIParser` | Parses orchestrator flags (`--workers`, `--cov`, `--report-json`) and forwards pytest options (`-k`, `-m`, `-v`, `--tb`, …) to each subprocess |
| `TestDiscovery` | Resolves `test_*.py` files from explicit targets or from `tests/` when no targets are given |
| `SubprocessTestExecutor` | Runs one test file per subprocess with `QT_QPA_PLATFORM=offscreen` and repo-root `PYTHONPATH` |
| `CoverageManager` | Assigns per-worker `COVERAGE_FILE` under `.coverage_parallel/`, then runs `coverage combine`, `coverage report`, and `coverage html` |
| `JsonReporter` | Writes optional machine-readable run summary (`--report-json`) |
| `run_parallel_tests()` | Main entry: discovery → worker pool → failure grouping → slowest-files report → optional JSON |

```text
make test / make test-cov
        │
        ▼
scripts/run_parallel_tests.py  (ThreadPoolExecutor)
        │
        ├── subprocess: pytest tests/test_a.py  (QT_QPA_PLATFORM=offscreen)
        ├── subprocess: pytest tests/test_b.py
        └── subprocess: pytest tests/test_n.py
        │
        ▼ (when --cov)
.coverage_parallel/.coverage.worker_*  →  coverage combine  →  report + htmlcov/
```

Structured logging (`logger.*` on stderr) complements CLI progress on stdout; see
`ai-tasks/PYPOST-1149/50-observability.md`.

## Makefile usage

The root `Makefile` defines a `WORKERS` variable with a computed default (not empty):

```makefile
WORKERS ?= $(shell PYTHONPATH=. python3 -c 'from scripts.run_parallel_tests import default_worker_count; print(default_worker_count())')
```

Default policy in `default_worker_count()` (PYPOST-1154):

```text
cpu = max(1, os.cpu_count() or 4)
workers = min(cpu + 2, 16)
```

Modest oversubscription for I/O-bound subprocess pytest; cap limits memory from many
concurrent Qt-heavy workers. On a 6-core host the default is eight workers.

| Target | Orchestrator invocation |
| --- | --- |
| `make test` | `scripts/run_parallel_tests.py --workers $(WORKERS)` + default `-m "not slow"` (unless `PYTEST_ARGS` overrides) |
| `make test-cov` | Same with `--cov` (combines worker coverage after all files finish) |

Examples:

```bash
make test                          # default workers from policy above
make test WORKERS=4                # four concurrent subprocesses
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
| `--cov` | Enable per-file coverage collection and post-run combine/report (`--cov=pypost`, `htmlcov/`). Also accepts `--cov=package` passthrough into pytest args. |
| `--report-json PATH`, `--report-json=PATH` | Write JSON summary after the run (see schema below). |

### Worker count precedence

1. CLI `--workers` / `-n`
2. Environment variable `WORKERS`
3. Environment variable `PYTEST_WORKERS`
4. `default_worker_count()` — `min(cpu + 2, 16)` where `cpu = max(1, os.cpu_count() or 4)`

### Pytest passthrough

These flags (and their values when required) are forwarded to **every** subprocess:

`-k`, `-m`, `-o`, `-c`, `-W`, `--override-ini`, `--ignore`, `--deselect`, `--tb`, `--capture`,
`--color`, `--maxfail`, plus other unknown `-` prefixed options.

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
    }
  ]
}
```

Exit codes: `0` when `RunSummary.is_success` (no failed files; coverage threshold failure
counts as a failure); `1` otherwise.

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
```

After completion:

- Grouped **FAILURES** section with stdout/stderr per failed file
- **TOP 5 SLOWEST FILES** ranking
- **SUMMARY** with wall-clock time, cumulative subprocess time, and speedup ratio

## Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Qt singleton / event-loop errors when raising `WORKERS` | Tests running in-process instead of via orchestrator | Use `make test`, not bare `pytest tests/` on the full suite; confirm `scripts/run_parallel_tests.py` exists |
| Segfault or EGL errors on Linux CI | Missing Qt runtime libraries on runner | CI installs packages via `.github/actions/install-qt-egl-runtime`; see [testing.md § Local vs CI parity](testing.md#local-vs-ci-test-parity-troubleshooting-pypost-723) |
| All files show SKIPPED, exit 0 | `-k` / `-m` filter matched no tests in some files | Expected (exit code 5 → skipped); tighten or change `PYTEST_ARGS` |
| `make test` ignores `WORKERS` | Override ignored or invalid env | Default is computed at Make parse time; pass `WORKERS=4` to override |
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
  --workers 2 --report-json /tmp/pypost-test-report.json -m "not slow"
```

## References

- [Testing via MCP and Prometheus](testing.md) — primary pytest/Makefile reference
- [GUI Testing](gui_testing.md) — Qt offscreen patterns and `qapp` fixture
- `ai-tasks/PYPOST-1149/20-architecture.md` — design rationale and diagrams
- `ai-tasks/PYPOST-1149/50-observability.md` — structured logging fields
