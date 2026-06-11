# PYPOST-457: Architecture

## Context

- `FunctionRegistry` owns the catalog (`allowed_names`, `get`, `is_allowed`).
- `register_into_env` binds catalog keys onto `jinja2.Environment.globals`.
- `TemplateService.__init__` constructs a default registry and calls `register_into_env`
  once on `self.env`.
- `FunctionExpressionResolver` uses `FunctionRegistry.is_allowed` for validation.

Parity invariant: for every `name` in `allowed_names()`, `env.globals[name] is registry.get(name)`.

## Approach

Tests-only delivery. No production code changes expected.

### Phase 1 — `FunctionRegistry` unit test

Add `test_catalog_allow_list_matches_env_globals` in `tests/test_function_registry.py`:

1. Create registry and empty `Environment`.
2. Call `register_into_env(env)`.
3. For each `name` in `allowed_names()`:
   - assert `name in env.globals`
   - assert `env.globals[name] is registry.get(name)`
   - assert callable

### Phase 2 — `TemplateService` integration test

Add `test_catalog_allow_list_matches_jinja_globals` in `tests/test_template_service.py`:

1. Use `TemplateService()` from `setUp`.
2. Iterate `svc._function_registry.allowed_names()` (private access acceptable in tests).
3. Assert same identity parity against `svc.env.globals`.

### Phase 3 — Dev docs

Update `doc/dev/template_expression_functions.md` known-gaps table: mark parity test done;
add PYPOST-457 to completed follow-ups list.

## Files Touched

| File | Change |
| --- | --- |
| `tests/test_function_registry.py` | New parity unit test |
| `tests/test_template_service.py` | New parity integration test |
| `doc/dev/template_expression_functions.md` | Gap table + completed list |

## Risks

- Low. If parity test fails, it indicates a real bug to fix rather than a test defect.
