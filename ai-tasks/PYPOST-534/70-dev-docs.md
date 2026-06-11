# PYPOST-534: Dev Docs

## Updated Files

- `doc/dev/environment_encryption_at_rest.md` — added **Selective re-encrypt benchmark
  (PYPOST-534)** section with CI test summary, local script usage, and sample output.

## Content Added

- How to run `tests/test_environment_save_selective_reencrypt_benchmark.py`.
- How to run `scripts/benchmark_env_save.py` with `--keys` and `--iterations`.
- Interpretation: reuse second save should show high `reused_count`, flat encryption metric, and
  faster timing than full re-encrypt.

## Cross-References

- PYPOST-485 — selective re-encrypt behavior under test.
- PYPOST-486 — async load/save (orthogonal).
