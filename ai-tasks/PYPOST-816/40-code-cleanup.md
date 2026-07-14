# PYPOST-816: Code Cleanup

## Changes

| Area | Change |
| --- | --- |
| `scripts/verify_ai_task_artifacts.py` | New verifier with roadmap parsing and baseline gate |
| `ai-tasks-artifacts-baseline.json` | Initial snapshot of 257 grandfathered legacy tasks |
| `Makefile` | Add `verify-ai-tasks`; include in `check` |
| `tests/test_verify_ai_task_artifacts.py` | Unit tests for parser, file sets, and baseline parity |
| `doc/dev/setup.md` | Note `make verify-ai-tasks` under artifact expectations |

## Verification

- [x] `make verify-ai-tasks` — pass (baseline match)
- [x] `make check` — pass (lint + tests + verifier)
- [x] No application runtime changes

## Checklist

- [x] Line length ≤ 100
- [x] UTF-8, LF endings
- [x] English comments and docs
- [x] `@pytest.mark.timeout` on test module
