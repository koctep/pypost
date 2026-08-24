# PYPOST-1154: Default WORKERS policy

## Problem

`WORKERS ?=` is empty in the Makefile, so `make test` omits `--workers` and
`get_worker_count()` falls back to `max(1, cpu_count())`. Benchmarks on 6-core ARM64 show
~16s faster wall clock with eight workers than six.

## Default policy

Single function `default_worker_count()` in `scripts/run_parallel_tests.py`:

```text
cpu = max(1, os.cpu_count() or 4)
default = min(cpu + 2, 16)
```

Rationale:

- `cpu + 2` — modest oversubscription for I/O-bound subprocess pytest (optimal 8 on 6 cores).
- Cap `16` — avoid excessive memory from many concurrent Qt subprocesses (PYPOST-1149 tech debt).

Examples:

| `cpu_count()` | Default workers |
| --- | --- |
| 2 | 4 |
| 4 | 6 |
| 6 | 8 |
| 8 | 10 |
| 16 | 16 |

## Makefile

- `WORKERS ?= $(shell PYTHONPATH=. $(PYTHON) -c "...default_worker_count()...")`
- `test` / `test-cov` always pass `--workers $(WORKERS)` (override via `make test WORKERS=4`).

## Script

`get_worker_count()` step 4 fallback calls `default_worker_count()` instead of raw `cpu_count()`.

## Failing repro plan (Step 3)

Add `test_default_worker_count_io_tuned_policy` in `tests/test_run_parallel_tests.py`:

- Patch `os.cpu_count` → 6, clear env, `cli_workers=None`
- Assert `get_worker_count()` == 8 (fails today with 6)

Add `test_makefile_test_target_passes_default_workers` in `tests/test_makefile.py`:

- Assert `test` recipe contains `--workers` and references `WORKERS`

## Tests to update

- `test_worker_count_precedence` docstring / fallback section

## Observability

No new logging — worker count already logged at run start. Document policy in dev docs only.

## N/A

No new runtime metrics; existing NOTICE log of worker count is sufficient.
