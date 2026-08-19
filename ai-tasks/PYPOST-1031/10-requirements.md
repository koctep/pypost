# PYPOST-1031: Include examples/README.md in docs relative link checker

## Programming Language

Python for link validator script and test contract, English Markdown for documentation.

## Goals

Follow-up from PYPOST-1026 (TD-5) and PYPOST-1015/PYPOST-1021. `examples/README.md` contains vital relative links to `doc/user/` and `examples/collections/` JSON fixtures. It must be checked automatically by `scripts/check_user_docs_links.py` and `tests/test_doc_user_relative_links.py`.

**Business goal:** Include `examples/README.md` in default target set of the relative link checker so fixture references and User Guide anchor links in `examples/README.md` are continuously validated.

## Definition of Done

- [ ] `scripts/check_user_docs_links.py` includes `examples/README.md` in `_DEFAULT_TARGETS`.
- [ ] `tests/test_doc_user_relative_links.py` includes `examples/README.md` in parametrized test suite.
- [ ] All tests and linters pass cleanly.
