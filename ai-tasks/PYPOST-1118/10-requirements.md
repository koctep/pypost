# Requirements: PYPOST-1118

## Overview

Add a built-in `env` template function to `FunctionRegistry` and `FunctionExpressionResolver` to allow template authors and request executions to safely resolve operating system environment variables (e.g. `{{ env(API_KEY) }}` or `{{ env(mcp.request.env_var) }}`).

## User Stories

- As a template author or developer executing requests, I want to reference operating system environment variables in template expressions (such as API keys, host configurations, or tokens) without having to manually duplicate them into environment variable profiles.
- As an MCP client or agent dispatching requests, I want to use expressions like `{{ env(mcp.request.env_var) }}` to dynamically resolve credentials and configurations from the host OS environment.

## Acceptance Criteria

1. **`_env` Implementation:**
   - Implement `_env(name: object) -> str` in `pypost/core/function_registry.py`.
   - Retrieve values from `os.environ`.
   - Safely handle missing keys by returning an empty string `""`.
   - Convert non-string input objects to strings via `str(name)` before looking up in `os.environ`.

2. **Catalog Registration:**
   - Register `env` in `_DEFAULT_CATALOG` in `pypost/core/function_registry.py`.
   - Expose `env` via `FunctionRegistry.allowed_names()`, `FunctionRegistry.is_allowed()`, `FunctionRegistry.get()`, and `FunctionRegistry.register_into_env()`.
   - Ensure `FunctionExpressionResolver` recognizes `env` as a permitted function expression.

3. **Template and Expression Support:**
   - Support standalone expressions: `{{ env(VAR_NAME) }}`.
   - Support safe dotted path arguments: `{{ env(mcp.request.env_var) }}`.
   - Support nested function calls: e.g. `{{ md5(env(SECRET_NAME)) }}`, `{{ to_int(env(PORT)) }}`, `{{ base64(env(DATA)) }}`, `{{ urlencode(env(QUERY)) }}`.
   - Maintain safety constraints: reject multi-argument calls, empty arguments, and unsafe attribute paths per standard resolver validation rules.

4. **Testing:**
   - Add unit tests in `tests/test_function_registry.py` with `os.environ` mocking (existing key, missing key, type conversion, registration).
   - Add unit tests in `tests/test_function_expression_resolver.py` validating valid and invalid syntax with `env`.
   - Add unit tests in `tests/test_template_service.py` verifying rendering and runtime/hover parity with `os.environ` mocking.

5. **Documentation:**
   - Update `doc/dev/template_expression_functions.md` with overview, architecture catalog update, supported functions list, detailed usage section, and examples.
