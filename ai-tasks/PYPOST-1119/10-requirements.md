# Requirements: PYPOST-1119

## Task Description

Allow environment profile variable values to contain template expressions (such as `{{ env(API_KEY) }}` or `{{ host }}:{{ port }}`), resolving them before applying variables to request templates and endpoints without requiring manual endpoint modifications.

## Acceptance Criteria

1. **AC 1: Pre-dispatch Evaluation**: Evaluate template expressions defined within environment profile variables prior to request dispatch and variable resolution.
2. **AC 2: Function & Cross-Variable Support**: Support built-in function expressions (such as `env`, `urlencode`, `md5`, `base64`, `to_int`) and cross-variable references within environment variable values.
3. **AC 3: Cycle Detection & Safe Fallback**: Safely detect and prevent circular reference cycles or infinite loops between variables with appropriate fallback or error handling.
4. **AC 4: Backward Compatibility**: Ensure full backward compatibility for environment profiles with static/plain string values.
5. **AC 5: Test Coverage**: Add unit and integration tests covering recursive resolution, cycle detection, and runtime/hover parity.
6. **AC 6: Documentation**: Update relevant developer and user documentation.

## Functional Requirements

- **FR-1**: When an environment profile contains variables referencing other variables in the same profile (e.g. `base_url = "http://{{host}}:{{port}}"` where `host = "localhost"` and `port = "8080"`), the referenced variables must be recursively resolved so `base_url` evaluates to `"http://localhost:8080"`.
- **FR-2**: When an environment profile variable contains built-in function calls (e.g. `api_key = "{{env(MY_API_KEY)}}"` or `auth = "Bearer {{base64(api_key)}}"`), functions must evaluate using the template function registry and current system environment/context.
- **FR-3**: Direct environment variable lookups via `{{env(VAR_NAME)}}` where `VAR_NAME` is the operating system environment variable name (not defined as a PyPost variable) must be supported, looking up `os.environ[VAR_NAME]`.
- **FR-4**: If a dependency cycle is encountered (e.g. `A -> B -> A` or `A -> A`), the resolution engine must detect the cycle, log a warning, and fall back to the unrendered/raw value without throwing unhandled exceptions or looping infinitely.
- **FR-5**: A recursion depth limit (`MAX_VARIABLE_RESOLUTION_DEPTH = 32`) must guard against arbitrarily deep or pathological reference chains.
- **FR-6**: Resolution must apply consistently across GUI execution (`RequestWorker` / `TabsPresenter` / `RequestWidget`), HTTP client (`HTTPClient`), MCP server (`MCPServerImpl` / `MCPServerRegistry`), cURL generation (`CurlGenerator`), and hover previews (`VariableHoverResolver` / `VariableHoverHelper`).
- **FR-7**: Static string values without `{{` must bypass recursive resolution with zero performance penalty.

## Non-Functional Requirements

- **NFR-1**: Thread-safety and immutability: environment variable resolution produces a new dictionary without mutating the underlying persisted `Environment.variables` dictionary.
- **NFR-2**: Performance: Fast-path return when no template delimiters (`{{`) exist across all profile values.
- **NFR-3**: Observability: Warning logs when cycles or depth limits are encountered; metrics tracking for template evaluations.
