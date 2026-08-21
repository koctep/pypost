# Code Cleanup: PYPOST-1119

## Summary of Code Changes

1. **New Module `pypost/core/environment_variable_resolver.py`**:
   - Implemented `EnvironmentVariableResolver` and `resolve_environment_variables` helper.
   - Efficient fast-path for profiles with static values (no `{{` check).
   - Dependency graph resolution with cycle detection and depth limit (`MAX_VARIABLE_RESOLUTION_DEPTH = 32`).
   - Clean, modular single-responsibility design.

2. **`pypost/core/function_registry.py`**:
   - Updated `_env` to extract `_undefined_name` when called with an undefined Jinja identifier, supporting `{{ env(VAR_NAME) }}` lookups directly.

3. **`pypost/core/template_service.py`**:
   - Exposed `resolve_environment_variables(variables, render_path)`.
   - Auto-resolves variables in `render_string` when input variables contain template expressions, guarding with `render_path != "env_resolve"` to prevent recursion.

4. **UI and MCP Integration**:
   - `EnvPresenter`: Evaluates environment variables before emitting `env_variables_changed` and updating snapshots.
   - `MCPServerImpl`: Resolves environment variables before merging with MCP arguments.
   - `VariableHoverResolver`: Resolves template expressions in variable reference chains.

5. **Linting and Quality Checks**:
   - Code formatted and checked with flake8 (0 errors).
   - All tests passing with fast execution times.
