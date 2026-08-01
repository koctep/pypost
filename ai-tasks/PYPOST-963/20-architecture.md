# PYPOST-963: Minimum slow-smoke pypost/ tree policy

## Research

PYPOST-943 added `_seed_installable_package` and a fast contract test for
pyproject-derived paths (`version.py`, `README.md`). TD-1 noted the stub-versus-mirror
decision remains implicit.

Committed packaging needs at editable-install time:

| Need | Satisfied by |
| --- | --- |
| Package discovery (`packages.find`) | Stub `pypost/__init__.py` |
| Dynamic version attr | Copied `pypost/version.py` |
| `[project] readme` | Copied `README.md` |
| Application modules (`core/`, `ui/`, …) | **Not required** for metadata resolution |

Full-checkout CI jobs have the real tree; slow smoke intentionally does not mirror it.

## Implementation Plan

1. Add `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` frozenset in `tests/test_makefile.py` next to
   `_seed_installable_package` — documents canonical stub paths under `pypost/`.
2. Add `test_slow_smoke_seed_materializes_minimum_pypost_tree` in
   `tests/test_makefile_install_seed_contract.py` — asserts seeded `pypost/` files match
   the policy constant exactly (no subdirs, no full mirror).
3. Extend `doc/dev/testing.md` § Slow smoke with explicit stub-versus-mirror policy and
   when to widen the constant.

No changes to seed helpers unless the new assertion reveals a mismatch (none expected).

## Architecture

| Component | Change |
| --- | --- |
| `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` | **Add** — single source of truth for stub tree |
| `_seed_installable_package` | **Docstring** — reference policy constant |
| Seed contract test | **Extend** — exact `pypost/` tree assertion |
| `doc/dev/testing.md` | **Extend** — policy prose + constant name |

## Design decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Policy location | `test_makefile.py` beside seed helper | Co-located with `_seed_installable_package` |
| Assertion style | Exact file set under `pypost/` | Catches over-seeding and under-seeding |
| Step 3 repro | N/A | No behavioral regression; additive guard |
