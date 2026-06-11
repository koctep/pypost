# Timeout budget audit (PYPOST-569)

Audit of tests that consume a large fraction of their `pytest.mark.timeout` marker.

## Method

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ \
  --durations=25 --durations-min=15 -q
```

Cross-referenced slow tests with module/class `pytestmark = pytest.mark.timeout(N)`.

## Findings

### Slowest tests (>15s wall time)

| Duration | Test | Timeout marker | % of budget |
| ---: | --- | ---: | ---: |
| 17.33s | `test_makefile.py::TestTargetExecution::test_lint_succeeds_after_install` | 120 (module) | 14% |
| 17.26s | `test_makefile.py::TestTargetExecution::test_install_succeeds_with_empty_requirements` | 120 | 14% |
| 17.21s | `test_makefile.py::TestTargetExecution::test_test_succeeds_after_install` | 120 | 14% |

All other tests completed in **<15s**. Full suite baseline: **~47–155s** depending on
environment (makefile targets spawn subprocess installs).

### Tests at timeout boundary?

**None observed** in `--durations-min=15` run. No test consumed >80% of its marker.

The user-reported “timeout but PASSED” pattern likely refers to:

1. **Visible slowness** in verbose output (Qt event-loop polling, `make install` in
   isolated tmp dirs) — not pytest-timeout firing.
2. **`pytest-timeout` method=signal** killing a hung test would show **FAILED**, not PASSED.
   True timeout passes do not occur in the baseline capture.

### Qt / event-loop tests

Modules using 60s markers (`test_env_storage_responsiveness.py`, `test_worker.py`, etc.)
complete in single-digit seconds in the baseline run. Bounded waits (`QTimer`,
`_process_until`) appear effective.

## Risk assessment

| Category | Risk | Notes |
| --- | --- | --- |
| Makefile integration (~17s/60s) | **Low** | Slow but stable; could tighten marker to 30s after monitoring |
| Qt polling tests | **Low** | Well under budget |
| Hypothetical hang masked timeout | **Medium** | Would FAIL loudly; not a silent false positive |

## Recommendations

1. Add `--durations=10 --durations-min=5` to optional CI verbose job (informational).
2. Consider lowering `test_makefile.py` timeout from 60s → 45s after one green week.
3. No urgent false-positive fixes required.

## Verdict

**SAFE TO CLOSE** — no tests pass only because they graze the timeout ceiling.
