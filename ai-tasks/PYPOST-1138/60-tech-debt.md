# PYPOST-1138: Technical Debt Analysis

## Shortcuts Taken

- **String and Regex Match Assertions in Doc Contract Tests**: In `tests/test_websocket_docs.py`, assertions verify section presence, UI object names, settings keys, hotkeys, and downgrade caveats via string membership and regex checks rather than Markdown AST parsing. This is fast and robust for current requirements, but may require manual updates if heading structures or phrase wordings change significantly.
- **Link Checker Scope**: `scripts/check_user_docs_links.py` was originally scoped for user documentation (`doc/user/*.md`). It was extended to verify referenced files and cross-links, but a comprehensive repository-wide documentation validator for all `doc/**/*.md` could be unified in a future refactor.

## Code Quality Issues

- **Documentation Verification Script Separation**: `scripts/lint_user_docs.py` and `scripts/check_user_docs_links.py` operate as separate scripts rather than a single unified documentation validator tool.

## Missing Tests

- **Dynamic Anchor Graph Traversal**: While link validity and anchor resolution are tested by `scripts/check_user_docs_links.py` and contract tests in `tests/test_websocket_docs.py`, full bidirectional cross-reference validation across all dev and user documentation is not yet completely automated in CI.
- **Python / pytest Timeouts**: All tests in `tests/test_websocket_docs.py` have explicit timeout markers configured via `pytestmark = pytest.mark.timeout(10)`, strictly conforming to testing requirements (no missing timeout blocker).

## Performance Concerns

- **Zero Runtime Overhead**: Documentation files and static contract test assertions have negligible performance footprint. `tests/test_websocket_docs.py` executes 14 assertions in ~0.04s.

## Follow-up Tasks

- **PYPOST-1148** (`NON-BLOCKER — pre-existing`): Full test suite deadlock under `make check` / `pytest` when running entire repository test suite in certain concurrency / Qt event loop environments. (Tracked under Jira issue PYPOST-1148).
- **Doc Tooling Unification**: Consolidate `scripts/lint_user_docs.py` and `scripts/check_user_docs_links.py` into a unified `doc_tools` utility that recursively discovers and validates all Markdown files across `doc/user/`, `doc/dev/`, and `doc/`.
