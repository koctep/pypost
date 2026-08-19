# PYPOST-1021: Add relative link checker for User Guide docs

## Programming Language

Python for link extraction and resolution logic and pytest test contracts, Makefile and GitHub Actions YAML for automation, English Markdown for documentation.

## Goals

Follow-up from PYPOST-1015 (TD-2). In PYPOST-1015, the User Guide structure was established with cross-references between topic pages, `doc/README.md`, and the root `README.md`. However, validation that relative file paths exist and section anchors resolve to valid headings was done via manual spot-checks.

**Business goal:** Implement an automated relative link and anchor validator in `scripts/check_user_docs_links.py`, wire it into `make check`, `make lint`, and CI, and protect it with tests in `tests/test_doc_user_relative_links.py`.

## Definition of Done

- [ ] `scripts/check_user_docs_links.py` verifies all relative file paths and `#anchor` targets in `doc/user/*.md`, `doc/README.md`, and `README.md`.
- [ ] `Makefile` provides `check-docs-links` and wires it into `make lint` / `lint-docs`.
- [ ] CI workflow `test.yml` runs `scripts/check_user_docs_links.py` during `Run lint`.
- [ ] `tests/test_doc_user_relative_links.py` validates all guide files and tests detection of broken files / anchors.
- [ ] All tests pass cleanly.
