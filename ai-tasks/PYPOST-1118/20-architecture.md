# Architecture: PYPOST-1118

## Overview

PYPOST-1118 introduces `env(name)` into PyPost's template expression engine. This allow-listed function allows template authors to resolve environment variables from the host operating system (`os.environ`) in template expressions such as `{{ env(API_KEY) }}` or `{{ env(mcp.request.env_var) }}`.

## Component Architecture

1. **`FunctionRegistry` (`pypost/core/function_registry.py`):**
   - Implements `_env(name: object) -> str` using `os.environ.get(str(name), "")`.
   - Registers `"env"` in `_DEFAULT_CATALOG`.
   - Binds `env` into Jinja's `Environment.globals` via `register_into_env()`.
   - Exposes `env` in `allowed_names()`, `is_allowed()`, and `get()`.

2. **`FunctionExpressionResolver` (`pypost/core/function_expression_resolver.py`):**
   - Automatically validates `env(...)` expressions against `FunctionRegistry.is_allowed("env")`.
   - Validates argument arity (single argument) and argument structure (safe path or nested function call).

3. **`TemplateService` (`pypost/core/template_service.py`):**
   - Compiles and renders Jinja templates containing `env(...)`.
   - Supports variable resolution for argument names (e.g. `variables={"API_KEY": "MY_KEY"}` resolves `env("MY_KEY")`).
   - Supports dotted paths (e.g. `variables={"mcp": {"request": {"env_var": "TOKEN"}}}`).
   - Preserves established fallback semantics on validation errors or unexpected exceptions.

## Security & Safety

- **Allow-list Enforced:** Only allow-listed catalog functions can be called. Arbitrary Python code execution remains impossible.
- **Safe Fallback on Missing Keys:** Missing keys in `os.environ` return empty string `""` without raising unhandled exceptions or breaking unrelated placeholders.
- **Safe Path Validation:** Underscore-leading attribute access (e.g. `{{ db.__class__ }}`) remains blocked by `_SAFE_PATH_RE`.

## Data Flow

```text
Template String ("Bearer {{ env(token_key) }}")
       │
       ▼
Tokenize (extract expression "env(token_key)")
       │
       ▼
FunctionExpressionResolver.validate_expressions()
       │ ── check catalog: "env" in FunctionRegistry.allowed_names()
       │ ── check arity: single argument "token_key"
       ▼
Jinja2 Environment Rendering
       │ ── resolve variable token_key -> "AUTH_TOKEN"
       │ ── execute _env("AUTH_TOKEN") -> os.environ.get("AUTH_TOKEN", "")
       ▼
Rendered Output ("Bearer secret-token-value")
```
