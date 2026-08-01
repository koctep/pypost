# PYPOST-966: Post-install pypost sanity in slow smoke

## Research

Current slow smoke (`TestSlowInstallSmoke.test_install_succeeds_with_project_pyproject`):

1. Materialize isolated workspace via `_materialize_slow_smoke_workspace`.
2. Run `make install` (network-heavy).
3. Run inline subprocess: `import pydantic` in `.venv/bin/python`.

PYPOST-943 TD-4 deferred `import pypost` to avoid Qt. The stub seed installs only
`pypost/__init__.py`, `pypost/version.py`, and script entry stubs — no UI tree.

**Version-module read** (`import pypost.version as v; assert v.__version__`) satisfies FR3
without traversing `pypost/__init__.py` side effects or UI subpackages.

## Implementation Plan

1. Add `POST_INSTALL_SANITY_SNIPPETS: tuple[str, ...]` beside slow-smoke helpers in
   `tests/test_makefile.py` — pydantic + pypost version read.
2. Add `_run_venv_python_snippet` and `_assert_post_install_sanity(bin_python)` helpers.
3. Refactor `TestSlowInstallSmoke` to call `_assert_post_install_sanity` after install.
4. Add fast contract test `test_post_install_sanity_includes_pypost_version_read` in
   `tests/test_makefile_install_seed_contract.py` (Step 3 red guard).
5. Document snippets and rationale in `doc/dev/testing.md` § Slow smoke.

## Architecture

| Component | Change |
| --- | --- |
| `POST_INSTALL_SANITY_SNIPPETS` | **Add** — declarative post-install checks |
| `_assert_post_install_sanity` | **Add** — runs snippets in installed venv |
| `TestSlowInstallSmoke` | **Refactor** — delegate to helper |
| Seed contract module | **Add** — fast snippet policy guard |

## Failing Repro Plan (Step 3)

Add `test_post_install_sanity_includes_pypost_version_read` asserting
`POST_INSTALL_SANITY_SNIPPETS` contains a `pypost` snippet. **Red** while snippets list only
`import pydantic`. Step 4 adds the version read snippet → green.

## Design Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Assertion style | `pypost.version.__version__` read | Avoids bare `import pypost` if `__init__` grows imports |
| Snippet registry | Module-level tuple | Fast contract + slow smoke share one source |
| Helper location | `test_makefile.py` | Slow smoke and seed helpers already live here |
