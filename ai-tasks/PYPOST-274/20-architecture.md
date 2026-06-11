# PYPOST-274: Architecture

## Research

- GNU Make exposes prerequisite graphs via `make -p` without executing recipes — suitable for
  static dependency assertions.
- Pytest subprocess tests in sibling modules (`tests/test_pytest_exit_policy.py`) already use
  isolated `tmp_path` workspaces with copied `Makefile`; same pattern avoids fixture drift.
- `pytest.ini` registers `slow` marker; `Makefile` `test` target passes `-m "not slow"` —
  verifiable by seeding a failing `@pytest.mark.slow` test and asserting `make test` still
  passes.

## Implementation Plan

1. Single module `tests/test_makefile.py` with shared helpers (`_run_make`, `_prerequisites`,
   `_seed_minimal_project`) and two fixtures (`make_workspace`, `make_workspace_full_deps`).
2. Organize tests into classes by concern: marker lifecycle, dependency chain, exit behavior,
   target execution, slow install smoke.
3. Keep fast tests under default `make test`; mark network-heavy full install
   `@pytest.mark.slow`.
4. Document scope in `doc/dev/testing.md` § Makefile automation tests.

## Architecture

```
tests/test_makefile.py
        │
        ├─ tmp_path fixture (isolated workspace)
        │     ├─ copied Makefile
        │     ├─ requirements.txt (empty or full)
        │     └─ minimal tests/ + pypost/ seed
        │
        ├─ _run_make() ──► subprocess make [targets]  (bounded timeout)
        │
        ├─ _prerequisites() ──► make -p parse (static dep graph)
        │
        └─ test classes
              ├─ TestMarkerLifecycle
              ├─ TestDependencyChain
              ├─ TestExitBehavior
              ├─ TestTargetExecution   ← PYPOST-277 lightweight smoke
              └─ TestSlowInstallSmoke  ← @pytest.mark.slow
```

| Class | PYPOST scope | Validates |
| --- | --- | --- |
| `TestMarkerLifecycle` | PYPOST-274 | Version marker create/remove/idempotence |
| `TestDependencyChain` | PYPOST-274 | `make -p` prerequisite chains |
| `TestExitBehavior` | PYPOST-274 | Exit codes for clean/unknown/bare venv |
| `TestTargetExecution` | PYPOST-277 | `venv-test`, `install`, `test`, `lint` smoke |
| `TestSlowInstallSmoke` | PYPOST-274 (optional) | Real `requirements.txt` install |

## Fixture design

| Fixture | `requirements.txt` | Use |
| --- | --- | --- |
| `make_workspace` | Empty comment stub | Fast targets, empty install |
| `make_workspace_full_deps` | Copied from repo root | Slow pydantic import smoke |

## Rejected alternatives

| Option | Verdict | Reason |
| --- | --- | --- |
| Test against repo `.venv` | Reject | Mutates developer environment; not hermetic |
| Shell script wrapper instead of pytest | Reject | No timeout markers; harder CI integration |
| Mock `subprocess` / Make | Reject | Would not catch real Make recipe failures |
| Single monolithic test | Reject | Hard to diagnose which contract broke |

## Files touched

| File | Change |
| --- | --- |
| `tests/test_makefile.py` | Makefile automation suite (expanded) |
| `doc/dev/testing.md` | Developer reference for scope and commands |
| `ai-tasks/PYPOST-274/*` | Workflow artifacts |

## Q&A

- **Does this duplicate PYPOST-307/310/559?** Those slices implemented the suite incrementally;
  PYPOST-274 is the umbrella debt closure from PYPOST-30 review.
