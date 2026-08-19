# PYPOST-1020: Architecture Design

## Markdown Linter Architecture

1. **`scripts/lint_user_docs.py`**:
   - Scope: `doc/user/*.md` (13 topic pages + README) and `doc/README.md`.
   - Rules:
     - Line length limit: maximum 100 characters per line outside code fences.
     - Trailing whitespace: forbidden on all lines.
     - ATX headers: `# Heading` required; missing space after `#` or Setext underlines (`===`, `---`) forbidden.
     - Bullet list consistency: `- ` marker required for unordered list items.
   - CLI: Supports standalone execution, custom file paths, standard exit codes (0 = clean, 1 = errors).

2. **Makefile and CI Integration**:
   - `lint-docs` target in `Makefile`.
   - `lint` target in `Makefile` executes flake8 and `lint_user_docs.py`.
   - `.github/workflows/test.yml` runs `scripts/lint_user_docs.py` in the `Run lint` step.

3. **Test Contract**:
   - `tests/test_doc_user_markdown_lint.py` parametrizes over all targets and tests error detection against synthetic violations.
