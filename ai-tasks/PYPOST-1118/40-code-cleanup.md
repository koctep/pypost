# Code Cleanup: PYPOST-1118

## Changes Made

1. **`pypost/core/function_registry.py`:**
   - Imported `os`.
   - Implemented `_env(name: object) -> str`.
   - Added `"env": _env` to `_DEFAULT_CATALOG`.

2. **`tests/test_function_registry.py`:**
   - Updated `test_allowed_names_matches_catalog` with `"env"`.
   - Added unit tests for `env` resolving existing keys, missing keys, converting non-string objects, and registration into Jinja environment.

3. **`tests/test_function_expression_resolver.py`:**
   - Added `test_env_function_validation_valid` covering standalone, dotted path, nested, and chained expressions.
   - Added `test_env_function_validation_invalid` covering multi-arg, empty-arg, and literal argument rejections.

4. **`tests/test_template_service.py`:**
   - Added unit tests verifying `env` rendering with variables, dotted paths, nested functions (`md5`, `to_int`, `base64`, `urlencode`), and runtime/hover parity.

5. **`tests/test_pypost_1077_verification_artifacts.py`:**
   - Updated catalog frozenset assertion to include `"env"`.

6. **`doc/dev/template_expression_functions.md`:**
   - Documented `env(name)` function in Overview, Architecture, Supported Functions, Usage, and Examples.

## Quality Checks

- `make lint` passed cleanly.
- `make typecheck` passed cleanly.
- `make lint-docs check-docs-links` passed cleanly.
- `make verify-ai-tasks` passed cleanly.
- Fast test suite passed with all tests green.
