# PYPOST-1397: Restore requirements-dev.txt lock parity

## Research

### Problem

`make check-lock-dev` recompiles `requirements-dev.in` with the repository `uv`
toolchain (`UV` resolved from PATH or `.venv/bin/uv`, CI-pinned `0.11.31`) and
diffs the body of the result against committed `requirements-dev.txt`. Current
checkout fails with:

```text
check-lock-dev: requirements-dev.txt is stale relative to requirements-dev.in
(run 'make lock-dev' and commit)
```

Observed drift is transitive / pin refresh against live index resolution (examples
from body diff): `certifi`, `coverage`, `flake8`, `filelock`, `msgpack`,
`mypy-extensions`, `pip`, `platformdirs`, `py-serializable`, `pyflakes`, and
related pins. Direct constraints in `requirements-dev.in` remain range-bounded
and are not being rewritten by this task.

### Existing machinery

| Component | Role |
| --- | --- |
| `requirements-dev.in` | Direct development dependency ranges |
| `requirements-dev.txt` | Committed transitive lock (output of `uv pip compile`) |
| `Makefile` `lock-dev` | Regenerates the lock (must match check resolution) |
| `Makefile` `check-lock-dev` | Fail-closed drift check with retry/backoff |
| `.github/workflows/test.yml` `check-lock-dev` | CI job running the same Make target |
| `tests/test_lockfile_verification.py` | Automated contract that `check-lock-dev` exits 0 |

**Root cause of “run make lock-dev” not clearing drift:** `uv pip compile -o`
onto an *existing* lock keeps prior pins unless `--upgrade` is set. `check-lock-dev`
compiles into a *new* `requirements-dev.txt.check`, so it always fresh-resolves.
Without `--upgrade` on `lock-dev`, the documented remediation cannot satisfy the
check. This task therefore (1) adds `--upgrade` to `lock-dev` only and (2)
refreshes `requirements-dev.txt`. The check contract is unchanged.

Prior art: PYPOST-1359 introduced the repro test, UV fallback discovery, and
`doc/dev/setup.md` guidance.

### Industry / toolchain notes

`uv pip compile` produces deterministic pins for a given index state and compiler
version. Re-running compile without changing `.in` is the supported remediation
when PyPI publishes newer matching releases inside declared ranges. Hand-editing
the `.txt` lock is out of policy.

## Implementation Plan

1. Keep `check-lock-dev`, CI job, and pytest contract fail-closed and unchanged.
2. Confirm red state with existing repro (Step 3).
3. Update `Makefile` `lock-dev` to pass `--upgrade` so regeneration matches the
   fresh resolve used by `check-lock-dev`.
4. Run `make lock-dev` to rewrite `requirements-dev.txt`.
5. Confirm green: `make check-lock-dev` and the existing pytest node.
6. Document cleanup, observability (N/A for new signals), tech debt, and docs.

**Mandatory — Failing Repro (next Step 3):** Use the existing automated test
`tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`.
It asserts desired behavior (`make check-lock-dev` exit 0; no stale message).
No new test file. Force failure without live product deps: the committed stale
lock already fails under current PyPI resolution. Sequence: confirm red →
`make lock-dev` → confirm green. Do not weaken asserts, add skip/xfail, or change
`check-lock-dev`.

## Architecture

```mermaid
flowchart LR
  IN["requirements-dev.in"] --> LOCKDEV["make lock-dev"]
  LOCKDEV --> TXT["requirements-dev.txt"]
  IN --> CHECK["make check-lock-dev"]
  TXT --> CHECK
  CHECK --> TEST["test_repro_check_lock_dev_detects_no_drift"]
```

- **No application module/API changes**.
- **Artifacts**: `Makefile` `lock-dev` gains `--upgrade`; regenerated
  `requirements-dev.txt`.
- **Interfaces**: Make targets remain the only supported operator surface.
  Sibling `lock` / `lock-otel` asymmetry is noted as follow-up tech debt.

## Q&A

- **Why not pin transitive packages in `.in`?** Ranges already express policy;
  the lock file is the pin surface. Expanding `.in` is a separate dependency
  policy change.
- **Why not change the check to ignore headers only?** It already strips the first
  two header lines; body drift is real and must fail closed.
