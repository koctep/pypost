# PYPOST-1334: Code Cleanup Report

## Linter Fixes

`make lint` runs flake8 on `pypost/` only, so the two new test modules are not covered by the
gate. They were reviewed by hand against `.flake8` (`max-line-length = 100`,
`extend-select = T201`) and the default pycodestyle/pyflakes rules:

- Fixed: E203 whitespace before `:` in a slice,
  `lines[header_index + 1 :]` → `lines[header_index + 1:]`
  (`tests/test_github_mcp_collection.py`,
  `test_github_makefile_path_freshness_target_declared`).
- Style: `classic[: len("ghp_") + 36]` → `classic[:len("ghp_") + 36]` so slices are written
  the same way (`test_github_fixtures_secret_scan_rejects_ghp_and_github_pat_values`).
- Checked, nothing found: unused imports, unused locals, unused module-level names, F541
  f-strings without placeholders, bare `except`, E711/E712, E731, E741, F811, invalid escape
  sequences, blank-line rules (E302/E303), trailing whitespace, final newline, `print` (T201).

## Code Formatting

Applied formatting changes:

- [x] Automatic code formatting: not applied. The repo has no formatter target, and the
  hand-wrapped spec table stays as written so the diff stays small.
- [x] Indentation and alignment fixes: none needed.
- [x] Line length correction: none needed. All five touched Python files are at or under 100
  characters per line.
- [x] JSON fixtures (`github_mcp.json`, `github_mcp_rest_paths.json`, `github.json`) checked:
  each one matches canonical `json.dumps(indent=2)` output plus a final newline, the same as
  the GitLab pair.
- [x] `tests/helpers/github_mcp_collection_http.py`: the module docstring paragraph was
  reflowed (it had a short wrapped line). Only the wording layout changed.

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: 0 (none present).
- Removed unused variables: 0 (none present).
- Removed commented-out code: none present.
- Removed debug prints: none present.
- Naming: in `test_github_numeric_identifier_paths_accept_decimal_strings_and_integers`, the
  local `description` held an `McpToolParam`. It is renamed to `parameter`, so the code now
  reads `parameter.description` instead of `description.description`.
- Docstrings (lsr-python): added one-line docstrings to the four `ToolSpec` properties
  (`request_id`, `repository_scoped`, `body_args`, `is_write`). Private helpers and test
  functions without docstrings follow the sibling `tests/test_gitlab_mcp_collection.py`
  convention (descriptive names, docstrings on public checkers and mutation twins). They
  are left unchanged.
- Inventory edits in `tests/test_examples_modernization.py`,
  `tests/test_predefined_library_pypost_1281_repro.py` and
  `tests/test_gitlab_mcp_collection.py`, plus the `Makefile` target, were reviewed. They are
  clean and nothing was changed.

All edits are behaviour-preserving. No assertion, parametrization, test id or collection
contract changed.

## Validation Results

Validation results:

- [x] All tests passed:
  `make test WORKERS=1 PYTEST_ARGS='tests/test_github_mcp_collection.py
  tests/test_examples_modernization.py tests/test_predefined_library_pypost_1281_repro.py
  tests/test_gitlab_mcp_collection.py -q'` exited 0 (4/4 files passed).
  `make check-github-mcp-path-freshness` exited 0 (2 passed).
- [x] All tests have explicit timeout markers. The module-level `pytestmark` sets
  `timeout(30)` and the loopback e2e test sets `@pytest.mark.timeout(60)`. The edited
  inventory modules keep their existing markers.
- [x] No merge conflicts.
- [x] Syntax is valid (`make lint` exit 0; the test modules import and run).
- [x] Types: no `pypost/` change. `make typecheck` is not part of this step's gate because of
  the known pre-existing failure PYPOST-1337.

## Notes

- `examples/README.md` has a few lines over 100 characters: the GitHub coverage table rows
  and the extended "Bundled collections" link list. Markdown table rows cannot be wrapped,
  and the link list was already over 100 characters before this task. The `doc/user` lint
  in `make lint` does not cover `examples/`. These lines are left as they are.
- Known pre-existing failures that this step does not fix: PYPOST-1337 (mypy baseline gate),
  PYPOST-1338 (import perf flake), PYPOST-1315 (export UI crash), PYPOST-1299 (exit policy).
