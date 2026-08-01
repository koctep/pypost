# PYPOST-927: CI check-lock architecture

## Research

- PYPOST-804 added `check-lock-dev` job: checkout → pinned `astral-sh/setup-uv` →
  `make check-lock-dev` → job summary.
- PYPOST-779 added Makefile `check-lock` for production lock verification (same compile/diff
  pattern as dev).
- `doc/dev/testing.md` documents dev lock CI; production lock remains local-only until this task.
- No pytest currently asserts the production lock CI job exists (gap this task closes via contract
  test + workflow change).

## Implementation Plan

**Failing Repro (Step 3):** Add `tests/test_ci_check_lock_job.py` asserting `.github/workflows/test.yml`
contains a top-level `check-lock` job that:

1. Uses `astral-sh/setup-uv` (pinned SHA comment pattern).
2. Runs `make check-lock` in a verify step.

Test fails today because only `check-lock-dev` exists. Step 4 adds the sibling job.

**Development (Step 4):** Insert `check-lock` job in `.github/workflows/test.yml` immediately
before `check-lock-dev`, mirroring PYPOST-804 structure with production Makefile target.

## Architecture

### Components

| Component | Responsibility |
| --- | --- |
| GitHub Actions job `check-lock` | Run once per workflow; install uv; delegate to Makefile |
| Makefile `check-lock` | Compile `requirements.in` and diff body vs committed `requirements.txt` |
| Contract test | Prevent regression — job must exist and invoke `make check-lock` |

### Dependency graph

```
requirements.in
        │
        ▼
  uv pip compile (Makefile check-lock)
        │
        ▼
  diff vs requirements.txt ──► CI job pass/fail
```

### Module interaction

```
.github/workflows/test.yml
        │
        ├── checkout
        ├── astral-sh/setup-uv (pinned)
        ├── make check-lock  ──► Makefile check-lock target
        └── job summary
```

## Q&A

| Question | Answer |
| --- | --- |
| Job placement? | Sibling before `check-lock-dev` — production lock gates runtime deps |
| Contract test vs integration? | Static YAML contract only; CI job is the integration test for drift |
| Add to `make check`? | No — same as `check-lock-dev` (uv not required for local gate) |
