# PYPOST-984: Dev Docs Summary

## Updated files

| File | Change |
| --- | --- |
| `doc/dev/setup.md` | Dependency lock file § documents the retry/backoff loop, the two distinct `stderr` messages, and the scratch-file cleanup |
| `doc/dev/testing.md` | CI lock verification § notes the pinned `uv` version and retry-before-fail behavior |

The `uv` version-pin cross-reference in `doc/dev/setup.md` (change 1 of the architecture) was
already added in Step 4; this step covers the remaining change 2 (Makefile retry/diagnostics)
and verifies the Step 4 cross-reference is still accurate and complete.

## Key maintainer workflow (unchanged, now more precise)

1. Edit direct production pins in `requirements.in`.
2. Run `make lock` (requires `uv`; install the version pinned in `.github/workflows/test.yml`'s
   `check-lock` job for CI/local parity).
3. Commit both `requirements.in` and `requirements.txt`.
4. Run `make check-lock` (or `make check`) locally; a transient `uv pip compile` failure now
   retries automatically instead of failing the gate outright.

## Cross-links

- Production lock introduction: `doc/dev/setup.md` § Dependency lock file (PYPOST-779)
- `uv` version pin: `doc/dev/setup.md` § Dependency lock file (PYPOST-984), workflow YAML is the
  single source of truth for the pinned value
- CI job description: `doc/dev/testing.md` § CI lock verification (PYPOST-804, PYPOST-927,
  PYPOST-984)
- Contract tests: `tests/test_ci_check_lock_job.py`, `tests/test_makefile_check_lock_retry.py`

## Verification

Grepped `doc/` for `check-lock`: only `doc/dev/setup.md` and `doc/dev/testing.md` reference it;
both were reviewed and now describe the retry/diagnostics/cleanup behavior added in Step 4.
No other `doc/dev/` file, `doc/README.md`, or `doc/dev/README.md` index entry needed changes —
the task adds no new public API, module, or feature, only hardens an existing CI/Makefile gate.
