# PYPOST-1021: Architecture Design

## Relative Link Checker Architecture

1. **`scripts/check_user_docs_links.py`**:
   - Scope: `doc/user/*.md`, `doc/README.md`, `README.md`.
   - Resolution algorithm:
     - Parses markdown links `[label](target)`.
     - Ignores external schemes (`http://`, `https://`, `mailto:`, `conversation:`, `file:`).
     - Resolves relative file path relative to referencing file directory.
     - Resolves `#anchor` target against heading slugs generated from target file headings or explicit HTML anchor tags (`id`/`name`).
   - CLI: Supports standalone invocation, custom file targets, standard exit code (0 = all valid, 1 = errors).

2. **Integration**:
   - Makefile targets: `check-docs-links`, `lint-docs`, `lint`.
   - CI workflow: `.github/workflows/test.yml` `Run lint` step.

3. **Test Contract**:
   - `tests/test_doc_user_relative_links.py` validates all guide files and tests detection of missing target files and invalid anchor references.
