# PYPOST-779: Lock file architecture

## Approach

Adopt the **pip-tools pattern** using **uv** as the compiler:

```
requirements.in  ──(uv pip compile)──►  requirements.txt
     ▲                                        │
     │ edit direct pins                      │ pip install -r
     │                                        ▼
  maintainer                            make install / CI
```

## File roles

| File | Maintainer action | Consumer |
| --- | --- | --- |
| `requirements.in` | Edit direct deps and constraints | `make lock` input |
| `requirements.txt` | Regenerate only via `make lock` | `make install`, CI, `pip-audit` |

## Toolchain

- **Compiler:** `uv pip compile requirements.in -o requirements.txt --python-version 3.11`
- **Verification:** `make check-lock` (diff compiled output against committed file)
- **Install:** unchanged `pip install -r requirements.txt` in venv and CI

## CI integration

- All three workflow jobs install from `requirements.txt`.
- `cache-dependency-path` includes both `requirements.in` and `requirements.txt` so cache
  invalidates when either file changes.
- `security-audit` job continues `pip-audit -r requirements.txt` (now fully pinned graph).

## Python version strategy

Lock compiled for **3.11** (repo minimum). Diff against 3.13 compile shows only stdlib
backport packages (`backports-tarfile`, `importlib-metadata`) differ; installing the 3.11 lock
on 3.13 is safe (extra packages are harmless).

## Makefile targets

| Target | Purpose |
| --- | --- |
| `lock` | Regenerate `requirements.txt` from `requirements.in` |
| `check-lock` | Fail if committed lock is stale |
| `install` | Unchanged — installs locked `requirements.txt` |

`lock` / `check-lock` require `uv` on PATH; not installed into `.venv`.

## Documentation updates

- `doc/dev/setup.md` — lock workflow and upgrade steps
- `doc/dev/dependencies_audit.md` — mark R-P2-001 done
- `doc/dev/testing.md` — CI cache key includes both lock files
