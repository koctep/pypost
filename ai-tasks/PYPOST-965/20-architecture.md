# PYPOST-965: Shared slow-smoke workspace assembly

## Research

Current duplication (pre-change):

| Location | Steps |
| --- | --- |
| `make_workspace_full_deps` fixture | copy Makefile → `_copy_pyproject` → `_seed_installable_package` |
| `_materialize_slow_smoke_seed` (contract test) | identical three steps |

Both paths must stay aligned whenever Makefile copy, pyproject wiring, or seed order changes.

## Implementation Plan

1. Add `_materialize_slow_smoke_workspace(workspace: Path) -> None` in `tests/test_makefile.py`
   immediately after `_copy_pyproject` — owns the three-step sequence.
2. Change `make_workspace_full_deps` to call the helper and return `tmp_path`.
3. Remove `_materialize_slow_smoke_seed` from `tests/test_makefile_install_seed_contract.py`;
   import and call `_materialize_slow_smoke_workspace` instead.
4. Note helper name in `doc/dev/testing.md` § Slow smoke isolated workspace seed.

No changes to `_seed_installable_package`, parser, or policy constant.

## Architecture

| Component | Change |
| --- | --- |
| `_materialize_slow_smoke_workspace` | **Add** — single assembly entry point |
| `make_workspace_full_deps` | **Refactor** — delegate to helper |
| `_materialize_slow_smoke_seed` | **Remove** — replaced by import |
| Seed contract tests | **Refactor** — call shared helper |

## Design decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Helper location | `test_makefile.py` beside seed helpers | Fixture and seed logic already live here |
| Helper visibility | Module-level `_` prefix | Test-only; imported by contract module |
| Step 3 repro | N/A | Refactor preserves behavior; contract tests are the guard |
