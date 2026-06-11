# PYPOST-534: Code Cleanup

## Lint and Format

- New test module and script follow project line-length limits.
- No production code changes; existing adapter and storage paths unchanged.

## Review Notes

- Benchmark helpers (`_enable_encryption`, `_large_environment`) are local to the test module.
- Profiling script is standalone under `scripts/` with argparse and median timing.
- No dead code or debug prints introduced.

## Files Touched

- `tests/test_environment_save_selective_reencrypt_benchmark.py`
- `scripts/benchmark_env_save.py`
