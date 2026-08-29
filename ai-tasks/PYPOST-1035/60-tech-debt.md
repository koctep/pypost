# PYPOST-1035: Technical Debt Analysis

## Shortcuts Taken

None. The implementation strictly fulfills the requirements and architecture by providing comprehensive automated unit test locks for safe dotted variable path arguments across catalog functions (`urlencode`, `md5`, `base64`, `to_int`, `env`) in both expression validation (`FunctionExpressionResolver`) and nested dictionary rendering (`TemplateService`). No production workarounds, temporary crutches, or bypasses were introduced.

## Code Quality Issues

None identified in the codebase or newly added tests.
- All test additions follow PEP 8 and project style conventions.
- Test modularity is preserved: `tests/test_function_arg_safe_paths.py` provides an isolated, comprehensive contract test suite for safe/unsafe dotted paths and nested calls, while `tests/test_function_expression_resolver.py` and `tests/test_template_service.py` integrate regression coverage into the existing core test suites.
- No dead code, debug prints, or unused imports were introduced.

## Missing Tests

None for the scope of PYPOST-1035.
- Validation of allowed catalog functions with single-argument safe dotted paths (`urlencode`, `md5`, `base64`, `to_int`, `env`) is fully covered.
- Validation of nested allowed function chains with safe dotted paths is covered.
- Rejection of unsafe attribute access patterns (e.g., `db.__class__`, `mcp.request.__class__`, `data._private`, `nested.__dict__`, `mcp.request.__globals__`) is locked with expected error codes (`invalid_argument`, `invalid_syntax`).
- Rendering of nested dictionary variable lookups through dotted arguments across catalog functions is verified in `TemplateService.render_string`.
- **Timeout Marker Review**: All new and modified test files declare explicit module-level timeout markers (`pytestmark = pytest.mark.timeout(30)`), strictly adhering to `do-testing` requirements. No blocker.

## Performance Concerns

None. The tests execute in sub-second timeframes and operate strictly on in-memory AST and dictionary data structures without disk or external network I/O. Production performance remains unaffected as no changes were made to runtime evaluation loops.

## Follow-up Tasks

### Pre-existing Base Non-blockers

The following pre-existing, unrelated base non-blockers were cataloged in previous sprint tasks and remain tracked:
- **PYPOST-1231**: Pre-existing non-blocker tracked in sprint backlog.
- **PYPOST-1232**: Pre-existing non-blocker tracked in sprint backlog.
- **PYPOST-1233**: Pre-existing non-blocker tracked in sprint backlog.
- **PYPOST-1234**: Pre-existing non-blocker tracked in sprint backlog.
- **PYPOST-1241**: Pre-existing non-blocker tracked in sprint backlog.

### Related TD-3 Follow-up

- **PYPOST-1036** (TD-3 from PYPOST-1033): Expand safe-path grammar locks: reject leading/trailing `.`, empty segments, and underscore-leading attribute segments beyond `__class__` (e.g. `mcp.request._private`); optionally assert a deep-but-safe path still validates.

No new technical debt follow-up tickets are required for PYPOST-1035.

## Verdict

**PASS / SAFE TO PROCEED**

All requirements from `10-requirements.md` and `20-architecture.md` are satisfied. The test locks for safe dotted function arguments and unsafe attribute rejection are solid, clean, and fully green with proper timeout markers. No blocking technical debt or architectural deviations exist. Ready for Step 8 (Dev Docs).
