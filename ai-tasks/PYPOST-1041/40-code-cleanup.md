# PYPOST-1041: Code Cleanup Report

Scope of the task diff (unchanged by this step):

- `tests/test_display_role_scan_ownership.py` — modified (`_module_all_exports` helper plus the
  AC-1/AC-2/AC-3 ownership assertions)
- `tests/test_display_role_scan_ownership_repro.py` — new (5 Step 3 repro tests)

No production module was touched in Step 4 or Step 5: `pypost/agent/tree_index.py` already
satisfied the contract the strengthened suite now locks.

## Linter Fixes

- `make lint` (flake8 on `pypost/` + Markdown and link checks) — clean before and after cleanup.
  The Makefile `lint` target scopes flake8 to `pypost/`, so neither touched file is in its path.
- Applied the repo's `.flake8` conventions manually to both test files instead:
  - Fixed: one 111-character line (`_MUTANT_TREE_INDEX_TEMPLATE` opening docstring) now 82 —
    all lines in both files are ≤ 100 characters.
  - Fixed: a 100-character `if not (...)` condition in `_has_find_child_delegation_check` was
    split into a named `names_display_role_equals` predicate (readability, and it no longer sits
    exactly on the limit).
  - Checked: no trailing whitespace, no `print` (`extend-select = T201`), no unused imports.
- `make test PYTEST_ARGS="tests/test_lint_pytestmark_e402.py"` still fails, and its 642-hit
  E402 findings come from `tests/test_examples_modernization*.py` and
  `tests/test_ui_library_manager.py` — pre-existing at base `253403db` and on the known
  non-gap list. Both PYPOST-1041 files declare `pytestmark` *after* all imports, so they
  contribute zero E402 findings.

## Code Formatting

Applied formatting changes:

- [x] Automatic code formatting — repo pins no formatter (`pyproject.toml` has no
      `[tool.black]`/`[tool.isort]`); style matched to the surrounding `tests/` modules by hand
- [x] Indentation and alignment fixes — mutant source constants re-indented as one template
- [x] Line length correction — 2 lines rewrapped; both files now ≤ 100 characters

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: 0 (none were present)
- Removed unused variables: 0
- Removed commented-out code: none
- Removed debug prints: none
- Removed duplication (`tests/test_display_role_scan_ownership_repro.py`):
  - The two ~35-line mutant module sources were near-identical. They are now generated from a
    single `_MUTANT_TREE_INDEX_TEMPLATE` with two named substitutions (`{exports}`,
    `{find_child}`), so each mutant *structurally* varies exactly one axis. This makes the
    Step 4 iteration-2 requirement — "the inline mutant gets a compliant `__all__` so it
    isolates a single contract violation" — impossible to break by accident.
  - The mutant signatures now mirror the real `pypost/agent/tree_index.py`
    (`model, text, parent=None` → `QModelIndex | None`) instead of a fictional
    `(model, parent, display_text, column)` API that could mislead a reviewer. Mutants are
    parsed, never imported, so this is AST-shape-only.
  - Extracted `_calls_to(tree, func_name)` — one AST call-site walker now shared by the three
    `_has_*_check` helpers (was inlined 3x, including a near-duplicate `_calls_helper`, which
    was deleted).
  - Extracted `_refers_to_find_child(arg)` — the "does this argument denote `find_child`"
    branch was duplicated between `_has_find_child_delegation_check` and
    `_has_find_child_forbids_display_role_check`.
  - Extracted `_patch_tree_index_source(monkeypatch, source)` — both mutation tests repeated the
    same `real_parse` / `mock_parse` / `monkeypatch.setattr` block; each test body is now 2 lines.
- Tightened naming:
  - `target_mod` → `ownership_suite` (says what the imported module *is*).
  - `mock_parse` → `fake_parse` (it is a stub, not a mock).
  - `_MUTANT_INLINE_DISPLAY_ROLE_CODE` / `_MUTANT_EMPTY_ALL_EXPORTS_CODE` kept as the public
    mutant names; their building blocks are `_COMPLIANT_EXPORTS`, `_EMPTY_EXPORTS`,
    `_COMPLIANT_FIND_CHILD`, `_INLINED_FIND_CHILD`.
- Docstrings and comments:
  - Repro module docstring listed 4 gaps for 5 tests; it now lists all 5 and states which tests
    read source versus which run the suite against a mutant.
  - `_has_all_exports_check` and the `..._forbids_inline_display_role` test had PEP 257-invalid
    docstrings (summary wrapped across two lines); rewritten as a one-line summary plus body.
  - Added a block comment above the mutant constants explaining that they are parsed, never
    imported, and why they mirror the real module.
  - `_module_all_exports` docstring now documents the empty-set fallback (missing `__all__`, or
    a non-list/tuple assignment) so a reader knows a missing manifest fails the caller's subset
    assertion rather than raising.
  - `test_flat_and_tree_share_display_role_match_helper` claimed only "AC-1"; it now enumerates
    AC-1 through AC-4, matching what the function actually asserts.
- Simplified `_module_all_exports`: `getattr(tree, "body", [])` → `ast.iter_child_nodes(tree)`
  (canonical stdlib direct-child iteration; no defensive `getattr` on a typed AST node).

## Validation Results

Validation results:

- [x] All tests passed — `make test PYTEST_ARGS="tests/test_display_role_scan_ownership_repro.py
      tests/test_display_role_scan_ownership.py"` → 2 files, 0 failed, 6/6 tests
      (1 ownership + 5 repro)
- [x] `make lint` clean
- [x] All tests have explicit timeout markers — both modules declare
      `pytestmark = pytest.mark.timeout(10)` after their imports (per `do-testing` and the
      PYPOST-1070 E402 rule)
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct — annotations added/kept on every helper
      (`_calls_to` returns `Iterator[ast.Call]`, `_refers_to_find_child` takes `ast.expr`);
      `make typecheck` scopes mypy to `pypost/core`, `models`, `ui`, so `tests/` is out of gate

### Refactor safety check

The repro helpers assert on the *source* of the ownership suite, so a refactor could silently
turn them into no-ops. Verified with a one-off AST script that each rewritten helper still
returns `False` against the base-commit (`git show HEAD:tests/test_display_role_scan_ownership.py`)
version and `True` against the current one:

| Helper | Base `253403db` | Current |
| --- | --- | --- |
| `_has_find_child_delegation_check` | `False` (red) | `True` |
| `_has_find_child_forbids_display_role_check` | `False` (red) | `True` |
| `_has_all_exports_check` | `False` (red) | `True` |

The regenerated mutants were checked the same way: the inline mutant has a compliant `__all__`,
does **not** call `display_role_equals`, and does inline `ItemDataRole.DisplayRole`; the
empty-exports mutant has `__all__ == []` with an otherwise compliant `find_child`. Each therefore
still trips exactly the assertion its test's `pytest.raises(match=...)` pattern expects.

## Notes

Deliberately left alone:

- **The duplicated `_calls_name` / `_has_display_role_attr` assertion pairs in
  `tests/test_display_role_scan_ownership.py`** (`find_child`, `find_tree`, `select_item`).
  Folding them into a loop or a shared `_assert_delegates(...)` helper looks like obvious
  dedup, but it would break the repro contract: `_has_find_child_delegation_check` and
  `_has_find_child_forbids_display_role_check` match an `ast.Call` whose *first argument* is a
  `Name` containing `"child"`. Behind a helper the argument becomes a generic `fn`, the repro
  tests go green-for-the-wrong-reason, and the mutation guard is lost. The repetition is
  load-bearing.
- **`_parse_file` in the repro duplicates `ownership_suite._parse`.** The repro must be able to
  detect a broken or deleted helper in the module it audits, so it parses independently rather
  than borrowing the subject's own parser.
- **Known non-gap failures** at base `253403db` (`test_agent_e2e_harness_table_doc`,
  `test_dialogs_audit`, `test_pypost_1077_verification_artifacts`, `test_environment_export`,
  `test_lint_pytestmark_e402`, `test_environment_export_ui`, `test_main_window_alert_reload`,
  `test_makefile`) — pre-existing and out of scope, not touched.
- **Full `make test`** was not re-run: it is known to segfault Qt workers and write a 110 MB core
  dump. Step 4 iteration 3 already recorded the full-suite triage against base `253403db`.

Ready for Step 6 (Observability) — expect N/A: this is a test-only, AST-assertion task with no
production code path and therefore no logs or metrics to add.
