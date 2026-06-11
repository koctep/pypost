# PYPOST-534: Observability

## Logging

No new log lines. Benchmark tests exercise existing `environment_serialized` output with
`encrypted_count` and `reused_count` at scale.

## Metrics

| Metric | Use in harness |
| --- | --- |
| `environment_value_encryptions_total` | Asserted stable after reuse second save |
| `environment_value_decryptions_total` | Not exercised (save-path benchmark) |
| `environment_encryption_errors_total` | Not exercised |

Reuse remains log-only per PYPOST-485; tests rely on encryption counter stability instead of a
dedicated reuse metric.

## Profiling script

`scripts/benchmark_env_save.py` prints median timings and stats to stdout for local runs; not
scraped by Prometheus.
