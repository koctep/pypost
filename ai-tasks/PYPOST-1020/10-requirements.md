# PYPOST-1020: Add Markdown lint for doc/user/ in make check or CI

## Programming Language

Python for linting logic and pytest contracts, Makefile and GitHub Actions YAML for automation, English Markdown for documentation.

## Goals

Follow-up from PYPOST-1015 (TD-1). In PYPOST-1015, the User Guide was introduced across 13 topic pages and an index under `doc/user/`. However, formatting and style validation (line length <= 100, trailing whitespace, ATX headers, bullet list consistency) was performed manually without automated CI or Makefile gates.

**Business goal:** Implement automated Markdown linting for `doc/user/*.md` and `doc/README.md` in `scripts/lint_user_docs.py`, wire it into `make lint` / `make check` and CI, and lock its behavior with tests in `tests/test_doc_user_markdown_lint.py`.

## Definition of Done

- [ ] `scripts/lint_user_docs.py` verifies line length <= 100, no trailing whitespace, ATX headers, and '-' bullet list markers across `doc/user/*.md` and `doc/README.md`.
- [ ] `Makefile` provides `lint-docs` and includes it in `make lint`.
- [ ] CI workflow `test.yml` runs `python scripts/lint_user_docs.py` during `Run lint`.
- [ ] `tests/test_doc_user_markdown_lint.py` validates all guide files and tests violation detection.
- [ ] All tests pass cleanly.
