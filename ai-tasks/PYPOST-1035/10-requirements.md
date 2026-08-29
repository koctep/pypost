# PYPOST-1035: Unit-test function-arg safe dotted paths (urlencode(mcp.request.*))

## Goals

When templating HTTP requests, users and MCP tool integrations need to pass dotted variable paths (such as `mcp.request.query` or `nested.payload.key`) as arguments to allowed template functions (e.g. `urlencode`, `md5`, `base64`, `env`).

In task PYPOST-1033, safe dotted variable path syntax was introduced and verified for plain variable placeholders. During technical debt review (TD-2), it was identified that the function argument branch (`_validate_function_args` in `FunctionExpressionResolver`) and nested value substitution via `TemplateService.render_string` require dedicated unit test locks to prevent regressions and guarantee consistent behavior across all allowed catalog functions.

**Programming language:** Python

## User Stories

- As a **collection author**, I want to use safe dotted variable paths inside allowed functions (e.g., `{{ urlencode(mcp.request.query) }}`), so that dynamic nested data can be transformed cleanly in request URLs, headers, and payloads.
- As a **maintainer**, I want comprehensive unit test coverage for function arguments with safe dotted paths, so that future parser or evaluator changes do not break nested function argument handling.
- As a **security-conscious operator**, I want unsafe attribute forms inside function arguments (such as `{{ urlencode(db.__class__) }}` or `{{ urlencode(mcp.request.__class__) }}`) to remain strictly rejected.

## Definition of Done

- [ ] Unit tests in `tests/test_function_expression_resolver.py` verify that `validate_content` and `validate_expressions` accept single-argument allowed functions containing safe dotted variable paths (e.g., `{{ urlencode(mcp.request.query) }}`, `{{ md5(mcp.request.body) }}`).
- [ ] Unit tests in `tests/test_function_expression_resolver.py` verify that unsafe attribute segments in function arguments (e.g., `{{ urlencode(db.__class__) }}`, `{{ urlencode(mcp.request.__class__) }}`) are rejected with appropriate error results (`invalid_argument` / `invalid_syntax`).
- [ ] Unit tests in `tests/test_template_service.py` verify that `TemplateService.render_string` evaluates nested dictionary values when passed as arguments to catalog functions (e.g., `{{ urlencode(mcp.request.query) }}`).
- [ ] All new tests include pytest timeout markers (`@pytest.mark.timeout(...)` or module-level `pytestmark`) per repository testing standards.
- [ ] Fast test suite (`make test`), lint checks (`make lint`), and verification checks (`make verify-ai-tasks` or `make check`) pass cleanly.

## Task Description

**Problem:** Task PYPOST-1033 updated `FunctionExpressionResolver` to support safe dotted variable paths (`_SAFE_PATH_RE`) in both standalone expressions and function arguments. While standalone paths like `{{ mcp.request.issue_key }}` were comprehensively tested, unit tests did not explicitly lock the function-argument branch of `_validate_function_args` or the corresponding `TemplateService.render_string` nested evaluation for functions taking dotted path arguments.

**Business outcome:** Ensure long-term stability and regression resistance for template function expressions that operate on nested data structures.

### In Scope

- Unit tests in `tests/test_function_expression_resolver.py` covering valid safe dotted paths as function arguments across catalog functions.
- Unit tests in `tests/test_function_expression_resolver.py` locking rejection of unsafe attribute access patterns inside function arguments.
- Unit tests in `tests/test_template_service.py` verifying that `render_string` resolves nested variables inside function arguments.
- Validation that existing behavior is preserved without breaking changes.

### Out of Scope

- Introducing new template functions or changing existing function semantics.
- Multi-argument function validation or grammar redesign.
- Jinja sandbox engine alterations.

## Functional Requirements

- `FunctionExpressionResolver.validate_content` and `validate_expressions` must evaluate single-argument allowed functions with safe dotted paths (e.g. `urlencode(mcp.request.query)`) as valid.
- `FunctionExpressionResolver.validate_content` and `validate_expressions` must evaluate single-argument allowed functions with unsafe dotted paths (e.g. `urlencode(mcp.request.__class__)`) as invalid syntax/argument.
- `TemplateService.render_string` must resolve nested dictionary variable references when passed to allowed catalog functions, substituting the transformed value into the template string.

## Non-functional Requirements

- **Test execution speed:** All unit tests must execute in sub-second timeframes with proper timeout decorators.
- **Code cleanliness:** Tests must conform to PEP 8 standards, pass `flake8` static analysis, and maintain consistent style with surrounding test suites.
- **Traceability:** Test cases should explicitly cross-reference PYPOST-1035 and TD-2.

## Constraints and Assumptions

- Issue type: Technical Debt / Unit Test Lock
- Jira key: PYPOST-1035
- Upstream ticket: PYPOST-1033 (TD-2 follow-up)
- Production implementation in `pypost/core/function_expression_resolver.py` already contains `_SAFE_PATH_RE`; this task locks and verifies behavior via automated unit tests.

## Main Entities

| Entity | Description |
| --- | --- |
| Template Expression | An expression inside `{{ ... }}` containing a function call |
| Catalog Function | An allow-listed single-argument transformation function (e.g., `urlencode`, `md5`, `base64`, `env`, `to_int`) |
| Safe Dotted Path | A variable identifier path consisting of dot-separated segments conforming to `_SAFE_PATH_RE` |
| Nested Context | A dictionary of template variables containing nested key-value mappings |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this task needed if PYPOST-1033 already implemented `_SAFE_PATH_RE`? | While `_SAFE_PATH_RE` was applied to both standalone expressions and function arguments, the test suite only locked standalone paths. Explicit unit tests are required to protect the function-arg branch from accidental regression. |
| Does this task require modifying production code? | Primarily unit tests. Production code will only be modified if existing logic fails to satisfy the specified safe dotted function argument requirements. |
| Which catalog functions should be tested with dotted arguments? | Common functions such as `urlencode`, `md5`, `base64`, `env`, and `to_int` to ensure broad coverage across transformation types. |
