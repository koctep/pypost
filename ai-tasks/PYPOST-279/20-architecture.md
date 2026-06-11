# PYPOST-279: Architecture

## Approach

Rely on **pytest native exit codes** end-to-end. No custom exit-code translation in the
Makefile, shell scripts, or GitHub Actions. Exit code `5` (no tests collected) propagates
unchanged from `python -m pytest` through `make test` and CI job steps. A small regression
module documents and guards the contract.

## Exit-code propagation

```
pytest (0 tests collected)
        │
        │ exit 5 (pytest built-in: EXIT_NOTESTSCOLLECTED)
        ▼
make test  ──►  subprocess exit 5  (Make forwards recipe exit status)
        │
        ▼
.github/workflows/test.yml  ──►  job step fails (non-zero shell exit)
```

| Layer | Mechanism | Exit 5 handling |
| --- | --- | --- |
| `pytest` | Built-in `EXIT_NOTESTSCOLLECTED = 5` | Emitted when collection yields zero tests |
| `Makefile` `test` target | `$(BIN)/python -m pytest tests/ ...` | No `|| true`, no `; exit 0` — recipe fails; make may surface exit `2` while reporting `Error 5` in stderr |
| GitHub Actions | `run: python -m pytest tests/ ...` | Step fails on non-zero; no special-case for 5 |
| Local `make test` | Same as Makefile row | Developer sees non-zero exit |

No additional wrapper is required: the policy is **“do not mask pytest exit codes.”**

## Regression test module

| Test | What it verifies |
| --- | --- |
| `test_pytest_returns_exit_code_5_for_empty_tests_dir` | Direct `python -m pytest` on empty `tests/` returns `5` |
| `test_make_test_fails_with_exit_code_5_when_no_tests_collected` | Isolated workspace: `make install` then `make test` with empty `tests/` exits non-zero and reports pytest `Error 5` |

### Fixture design

- **Isolated tmp workspace** — copy root `Makefile`, empty `requirements.txt`, empty `tests/`
  directory (no `test_*.py`). Mirrors `tests/test_makefile.py` pattern without touching repo
  `.venv`.
- **Subprocess bounds** — inner `subprocess.run(..., timeout=25)` plus outer
  `@pytest.mark.timeout(30)` on each test.
- **No pytest.ini in fixture** — exercises Makefile’s explicit `-m "not slow"` flag; zero
  collection still yields exit `5`.

## Rejected alternatives

| Option | Verdict | Reason |
| --- | --- | --- |
| Map exit `5` → `0` in Makefile | Reject | Hides misconfiguration; contradicts policy |
| Treat exit `5` as warning in CI | Reject | Warnings do not block merges |
| Custom pytest plugin to fail on empty | Reject | Native exit `5` already non-zero; extra code |
| Document-only (no tests) | Reject | Policy would drift without regression guard |

## Files touched

| File | Change |
| --- | --- |
| `tests/test_pytest_exit_policy.py` | New regression module |
| `ai-tasks/PYPOST-279/*` | Requirements and architecture artifacts |

No Makefile or workflow changes: existing behavior already satisfies the policy once
documented and tested.
