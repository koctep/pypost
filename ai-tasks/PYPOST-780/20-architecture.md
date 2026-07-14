# PYPOST-780: Dev dependency lock architecture

## Approach

Extend the **PYPOST-779 two-file lock pattern** to development tooling:

```
requirements-dev.in  ──(uv pip compile)──►  requirements-dev.txt
         ▲                                           │
         │ edit direct pins                         │ pip install -r
         │                                           ▼
    maintainer                              make venv-test / CI
```

## File roles

| File | Maintainer action | Consumer |
| --- | --- | --- |
| `requirements-dev.in` | Edit direct dev deps and constraints | `make lock-dev` input |
| `requirements-dev.txt` | Regenerate only via `make lock-dev` | `make venv-test`, CI test jobs |

## Toolchain

- **Compiler:** `uv pip compile requirements-dev.in -o requirements-dev.txt --python-version 3.11`
- **Verification:** `make check-lock-dev` (diff compiled output against committed file)
- **Install:** `pip install -r requirements-dev.txt` in `venv-test` and CI

## Makefile targets

| Target | Purpose |
| --- | --- |
| `lock-dev` | Regenerate `requirements-dev.txt` from `requirements-dev.in` |
| `check-lock-dev` | Fail if committed dev lock is stale |
| `venv-test` | Install pinned dev stack from `requirements-dev.txt` |

Production targets (`lock`, `check-lock`, `install`) unchanged except `venv-test` install source.

## CI integration

- Main `test` job: replace inline `pip install pytest …` with `requirements-dev.txt`.
- `make-install-smoke`: install full dev lock (superset of prior pytest-only install).
- `cache-dependency-path`: add `requirements-dev.in` and `requirements-dev.txt`.
- `security-audit` job: unchanged (production `requirements.txt` only).

## Python version strategy

Same as production lock: compile for **3.11** minimum; CI matrix 3.11 + 3.13 installs the
3.11 lock (stdlib backport diffs only, verified pattern from PYPOST-779).
