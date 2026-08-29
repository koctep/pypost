# Template Expression Functions (PYPOST-450–PYPOST-454, PYPOST-1037, PYPOST-1118)

## Overview

PYPOST-450 adds function expressions to template placeholders in all variable-enabled request
surfaces. Canonical syntax: function calls appear only inside `{{...}}`, for example
`{{urlencode(db)}}`.

PYPOST-451 extracts the function catalog into `pypost/core/function_registry.py`
(`FunctionRegistry`).

PYPOST-452 splits template-function validation responsibilities:

- `FunctionExpressionResolver` owns parsing and validation flow for `{{...}}` expressions.
- `ValidationResult` lives in `pypost/core/template_expression_types.py` as a shared type.
- `TemplateService` orchestrates environment setup, rendering, logging, and metrics, while
  delegating expression validation to the resolver.

PYPOST-453 aligns and documents the nested-function policy: allow-listed function calls may
nest recursively (for example `{{md5(urlencode(db))}}`). Policy is declared by
`NESTED_FUNCTION_CALLS_ALLOWED` in `function_expression_resolver.py` and enforced by the
existing recursive validation path.

PYPOST-454 adds acceptance tests for malformed nested expressions, whitespace-heavy
variants, and runtime/hover parity for those forms. Delivery is tests-only; observed
validation codes and fallback behavior are documented in the edge-case section below.

PYPOST-1033 extends plain-expression validation so **safe dotted variable paths**
(for example `{{ mcp.request.issue_key }}`) validate and render. This unblocks MCP
tool-argument substitution when execution variables include a nested
`mcp.request` dict. Underscore-leading attribute segments (for example
`{{ db.__class__ }}`) remain `invalid_syntax`.

PYPOST-1037 adds `to_int(value)`: an allow-listed conversion for the common
case where an MCP or other template caller supplies an integer identifier as
text.  It is deliberately narrow: only a single ASCII decimal string, with an
optional leading `+` or `-`, is accepted.  The special failure handling applies
only while an `HTTPClient` prepares an outbound request; it prevents an invalid
direct `to_int(...)` expression from being sent as a literal value.

PYPOST-1118 adds `env(name)`: an allow-listed template function retrieving
operating system environment variables from `os.environ`, safely returning an
empty string when the variable is unset and converting input objects to string.

Outside the narrow strict HTTP conversion boundary described below, implemented
behavior is backward compatible:

- Valid expressions are rendered through `TemplateService`.
- Invalid expressions fall back to original content (no hard request-time failure).
- Plain variable placeholders like `{{host}}` continue to work unchanged.
- Safe dotted paths are accepted; unsafe attribute-style paths stay rejected.
- Ordinary invalid expressions retain their literal-fallback behavior.  Invalid
  direct `to_int(...)` expressions are the narrow exception during HTTP request
  preparation, where dispatch is blocked before `session.request`.

### Plain Variable Tokenizer and Whitespace Handling (PYPOST-1151 / PYPOST-1176)

PyPost provides shared tokenizer helpers in `pypost/core/template_expression_tokenizer.py`
for distinguishing strict plain variable tokens from general/loose template expressions:

- `PLAIN_VARIABLE_PATTERN`: Strict regex `^\{\{([a-zA-Z0-9_]+)\}\}$` matching only unspaced,
  untrimmed identifiers inside double braces (e.g. `{{var}}`). Tokens with inner whitespace
  (such as `{{ var }}`, `{{  var  }}`, `{{\tvar\t}}`, `{{\nvar\n}}`) are rejected by
  `is_plain_variable_token` and return `None` from `extract_plain_variable_name`.
- `LOOSE_PLAIN_VARIABLE_PATTERN`: Permissive regex `^\{\{\s*([a-zA-Z0-9_]+)\s*\}\}$` for
  UI hover locators and forgiving context extraction where leading/trailing whitespace around
  identifiers is accepted via `is_loose_plain_variable_token` and `extract_loose_plain_variable_name`.

Unit tests in `tests/test_template_expression_tokenizer.py` enforce these whitespace contracts.

## Architecture

Main components:

- `pypost/core/function_registry.py` (`FunctionRegistry`)
  - Single source of truth for allow-listed template-callable names and implementations:
    `urlencode`, `md5`, `base64`, `to_int`, `env`.
  - Exposes `allowed_names()`, `is_allowed()`, `get()`, and `register_into_env(env)` to bind
    those callables onto `jinja2.Environment.globals` (catalog keys only).
- `pypost/core/template_expression_types.py` (`ValidationResult`)
  - Shared validation outcome dataclass with `is_valid`, `code`, and `function_name`.
  - Factory methods: `ValidationResult.valid()` and `ValidationResult.error(...)`.
- `pypost/core/function_expression_resolver.py` (`FunctionExpressionResolver`)
  - Parses and validates expressions inside `{{...}}`.
  - Accepts plain identifiers and **safe dotted variable paths** via `_SAFE_PATH_RE`
    (PYPOST-1033); same rule applies to function arguments.
  - Uses `FunctionRegistry` for allow-list checks at every call node, including nested chains.
  - Exposes `NESTED_FUNCTION_CALLS_ALLOWED` as the declarative nested-call policy constant.
  - Returns `ValidationResult` and does not emit logs or metrics.
- `pypost/core/template_service.py` (`TemplateService`)
  - Owns `jinja2.Environment`, registry wiring, render orchestration, logging, and metrics.
  - Delegates `validate_function_expressions(...)` and render-path validation to
    `FunctionExpressionResolver`.
  - Maps validation codes to user-facing messages only on the render fallback path.
- `pypost/ui/widgets/mixins.py` (`VariableHoverHelper`)
  - `EXPRESSION_PATTERN` aliases `TEMPLATE_PLACEHOLDER_PATTERN` from the core tokenizer
    (PYPOST-536) so hover token boundaries match validation.
  - Reuses `TemplateService.render_string(..., render_path="hover")` for function hover parity.
  - Keeps hidden-variable masking for plain variables via `HIDDEN_MASK`.
- `pypost/core/metrics.py` (`MetricsManager`)
  - Exposes counters for expression render attempts and validation failures.
- `pypost/core/http_client.py` (`HTTPClient`)
  - Renders URL, header keys/values, param keys/values, and body via
    `TemplateService.render_string` before outbound requests.
  - Uses the strict conversion render path for request preparation. A failed
    direct `to_int(...)` is mapped to `ExecutionError(TEMPLATE)` and stops the
    request before `session.request`.
- `pypost/core/request_service.py` (`RequestService`)
  - MCP/history paths render URL, headers, and body
    (`_execute_mcp` / PYPOST-1173).
- `pypost/ui/presenters/mcp_client_presenter.py` (`McpClientPresenter`)
  - MCP Client draft URL and header names/values via
    `resolve_outbound_fields` (PYPOST-1167).

### Context coverage matrix

Every variable-enabled surface uses the same validation + render pipeline. Header and param
name/value columns are separate render/hover surfaces.

| Context | UI surface | Render path | Hover path |
| --- | --- | --- | --- |
| Request URL | `RequestWidget.url_input` | `HTTPClient` → `render_string(url)` | `VariableAwareLineEdit` → `VariableHoverHelper` |
| Header names | `RequestWidget.headers_table` key column | `render_string(k)` per row | Table cell hover |
| Header values | `RequestWidget.headers_table` value column | `render_string(v)` per row | Table cell hover |
| MCP Client URL | `McpClientConnectionBar.url_input` | `McpClientPresenter.resolve_outbound_fields` | `VariableAwareLineEdit` |
| MCP Client header names | `McpClientHeadersTable` key column | `render_string(k)` per row | Table cell hover |
| MCP Client header values | `McpClientHeadersTable` value column | `render_string(v)` per row | Table cell hover |
| Param names | `RequestWidget.params_table` key column | `render_string(k)` per row | Table cell hover |
| Param values | `RequestWidget.params_table` value column | `render_string(v)` per row | Table cell hover |
| Request body | `RequestWidget.body_edit` | `render_string(body)` | `CodeEditor` hover mixin |
| Hover preview | All editors above | N/A (preview only) | `VariableHoverHelper.resolve_text` |

UI propagation: `env_presenter.py` → `tabs_presenter.py` → `RequestWidget` or
duck-typed `McpClientPresenter` / `WebSocketPresenter` supplies variable maps
and hidden keys to editors. Expression parsing happens only in core modules,
not in presenters.

## Usage/API

Primary API entry points:

- `TemplateService.render_string(content, variables, render_path="runtime")`
  - Validation-first render flow:
    1. Delegate validation to `FunctionExpressionResolver`.
    2. On invalid expression, log and emit validation metrics, then fall back to original
       content.
    3. On valid expression, render through Jinja.
    4. On render exception, emit render error metric and fall back to original content.
- `TemplateService.validate_function_expressions(content) -> ValidationResult`
  - Thin delegate to `FunctionExpressionResolver.validate_content(content)`.
- `FunctionExpressionResolver.validate_content(content) -> ValidationResult`
  - Resolver-level API for expression scanning and validation.
- `FunctionExpressionResolver.validate_expressions(expressions) -> ValidationResult`
  - Validates pre-tokenized inner expression strings (used by render path after a single
    scan).
- `TEMPLATE_PLACEHOLDER_PATTERN` (`template_expression_tokenizer`)
  - Compiled regex `\{\{\s*(.*?)\s*\}\}` shared by render, validation, and hover scans.
- `PLAIN_VARIABLE_PATTERN` (`template_expression_tokenizer`)
  - Compiled regex `\{\{([a-zA-Z0-9_]+)\}\}` for plain `{{name}}` tokens without inner
    whitespace. Used by hover fast-path (`VariableHoverHelper.VARIABLE_PATTERN`) and
    `is_plain_variable_token` / `extract_plain_variable_name` helpers (PYPOST-113).
- `is_plain_variable_token(token) -> bool` (`template_expression_tokenizer`)
  - True when the full token is a plain variable placeholder (not a function call).
- `extract_plain_variable_name(token) -> str | None` (`template_expression_tokenizer`)
  - Returns the captured name from a plain token, or `None`.
- `tokenize_template_expressions(content) -> list[str]` (`template_expression_tokenizer`)
  - Canonical extraction of inner text for each `{{ ... }}` placeholder.

Supported validation result codes:

- `unknown_function`
- `invalid_arity`
- `invalid_argument`
- `invalid_syntax`

Supported patterns:

- Plain variable: `{{host}}`
- Safe dotted variable path (PYPOST-1033): `{{ mcp.request.issue_key }}`
- Function call: `{{urlencode(db)}}`
- Function call with safe path argument (PYPOST-1033 / PYPOST-1035): `{{urlencode(mcp.request.query)}}`
- Nested function call: `{{md5(urlencode(db))}}`
- Deep chain (no fixed depth limit): `{{base64(md5(urlencode(db)))}}`

### Safe variable path grammar (PYPOST-1033)

`FunctionExpressionResolver` accepts a plain expression (or function argument) when it
matches `_SAFE_PATH_RE`:

| Segment | Pattern | Notes |
| --- | --- | --- |
| First | `[a-zA-Z_][a-zA-Z0-9_]*` | Same as a plain identifier; may start with `_` |
| Later (each `.` segment) | `[a-zA-Z][a-zA-Z0-9_]*` | Must **not** start with `_` |

Rules:

- One or more segments separated by `.` (no empty, leading, or trailing dots).
- Depth is not specially capped; product MCP paths are typically `mcp.request.<param>`.
- The resolver stays MCP-agnostic: any nested dict path that matches the grammar is valid.

| Expression | Result |
| --- | --- |
| `mcp.request.issue_key` | valid → Jinja renders nested dict access |
| `urlencode(mcp.request.query)` | valid (same path rule for arguments) |
| `db.__class__` | `invalid_syntax` (underscore attribute segment) |
| `mcp.request.__class__` | `invalid_syntax` |
| `db\|md5` / filter forms | `invalid_syntax` |

Supported functions:

- `urlencode(var)` -> URL-encoded string
- `md5(var)` -> hex MD5 digest
- `base64(var)` -> Base64-encoded string
- `to_int(var)` -> integer from a native Python `int` or one ASCII decimal string
  (PYPOST-1037, PYPOST-1038)
- `env(var)` -> operating system environment variable value, or empty string if unset
  (PYPOST-1118)

### Environment variable resolution (PYPOST-1118)

Use `env(...)` to safely retrieve operating system environment variables from
`os.environ`. The expression is available across all template-rendering surfaces:
URLs, header names and values, parameter names and values, and request bodies.

The argument provides the environment variable key name, which may be a variable
name, a safe dotted path (e.g. `mcp.request.env_var`), or the result of another
nested function call. If the environment variable is not defined in `os.environ`,
`env(...)` safely returns an empty string `""` without raising errors. Non-string
input objects are converted to strings before environment lookup.

| Request field | Template and variables | OS Environment | Prepared value |
| --- | --- | --- | --- |
| Header value | `Bearer {{env(api_key_name)}}`, `{"api_key_name": "SECRET_TOKEN"}` | `SECRET_TOKEN=my-secret-token` | `Bearer my-secret-token` |
| URL | `/items/{{env(mcp.request.env_var)}}`, `{"mcp": {"request": {"env_var": "ITEM_ID"}}}` | `ITEM_ID=100` | `/items/100` |
| Unset variable | `{{env(missing_var)}}`, `{"missing_var": "UNSET_KEY"}` | *(not set)* | `""` (empty string) |
| Nested hash | `{{md5(env(secret_key))}}`, `{"secret_key": "API_SECRET"}` | `API_SECRET=pass` | Hex MD5 of `pass` |

### Integer conversion for HTTP templates (PYPOST-1037, PYPOST-1038)

Use `to_int(...)` when the destination operation requires a whole-number value
and its source is either a native Python `int` or decimal text. The expression
is available wherever request templates are rendered: URLs, header names and
values, parameter names and values, and request bodies.

The one argument must resolve to a true `int` (not `bool`) or to a `str`
matching `[+-]?[0-9]+`. Native integers pass through unchanged. Whitespace,
decimal points, exponent notation, underscores, booleans, floats, `None`,
containers, other non-string values, empty strings, and non-ASCII digits are
rejected. The result is a Python `int`; string-oriented HTTP fields render its
decimal text, while an unquoted expression in a JSON body is parsed as a native
JSON integer.

| Request field | Template and supplied variables | Prepared value |
| --- | --- | --- |
| URL | `/items/{{to_int(issue_id)}}`, `{"issue_id": "42"}` | `/items/42` |
| Query parameter | `{"id": "{{to_int(issue_id)}}"}`, `{"issue_id": "42"}` | `{"id": "42"}` |
| JSON body | `{"id": {{to_int(issue_id)}}}`, `{"issue_id": "42"}` | `{"id": 42}` as the JSON request body |
| URL, native integer | `/items/{{to_int(issue_id)}}`, `{"issue_id": 42}` | `/items/42` |

Do not quote the expression in a JSON body when the API expects an integer:
`{"id": "{{to_int(issue_id)}}"}` intentionally produces a JSON string.
`to_int` does not change an external MCP schema or make every schema accept
strings; it lets a collection template create the required integer-shaped
request value.

#### Strict HTTP failure boundary

`TemplateService.render_string()` and hover callers retain the established
backward-compatible fallback: an invalid expression returns the complete
original field content. `HTTPClient` instead uses
`render_string_strict_conversion()` during request preparation. If a direct
`{{to_int(...)` expression fails because of an invalid value, wrong arity,
malformed/unclosed syntax, or a nested-expression failure, it raises
`ExecutionError` with `ErrorCategory.TEMPLATE`; `session.request` is not
called. This applies to URL, headers, parameters, and JSON bodies.

The boundary is intentionally precise, not a general change to template error
handling:

- `{{not_to_int(issue_id)}}`, `{{foo.to_int(issue_id)}}`, and text merely
  containing `to_int(` keep ordinary fallback behavior.
- A valid `{{to_int(issue_id)}}` in the same field as an unrelated invalid
  expression also keeps the ordinary complete-field literal fallback and may
  dispatch. The strict path blocks only when the `to_int` expression itself
  has failed.
- A `TemplateService` subclass that overrides `render_string(content,
  variables)` remains supported; the strict preflight protects conversion
  failures without changing that established injection seam.

#### Failure diagnostics and testing

On strict rejection, `pypost.core.http_client` logs the ERROR event
`template_integer_conversion_failed`. It includes the HTTP method and a
bounded, sanitized origin only. It never includes the failed input, headers,
parameters, body, URL user info, path, query, or fragment; malformed URLs use
`[invalid-url]`.

No new metric was added. Existing template metrics distinguish the path:

- Runtime conversion errors increment
  `template_expression_render_attempts_total{render_path="http",outcome="render_error"}`.
- Malformed or wrong-arity calls rejected during validation use
  `template_expression_validation_failures_total` and the existing
  `validation_error` outcome.

The regression suite in `tests/test_template_service.py` covers accepted and
rejected decimal grammar plus strict/fallback behavior. The `HTTPClient` suite
in `tests/test_http_client.py` covers native JSON integers, URL and parameter
rendering, every protected request context, no-dispatch assertions, safe logs,
metric outcomes, and legacy compatibility cases. Run the focused checks with:

```bash
PYTEST_ARGS='tests/test_template_service.py tests/test_http_client.py' make test
```

Examples:

- URL field: `/{{host}}/{{urlencode(db)}}`
- MCP tool args (nested context): `{{ mcp.request.issue_key }}` with
  `variables={"mcp": {"request": {"issue_key": "PROJ-1"}}}` → `PROJ-1`
- Environment variable: `{{ env(api_key) }}` or `{{ env(mcp.request.env_var) }}`
- Header/param/body values: `{{md5(secret)}}`, `{{base64(path)}}`
- Hover tooltip resolution uses the same render rules as runtime for function placeholders.
- Nested chain: `{{md5(urlencode(db))}}` with `db="a b"` → MD5 of URL-encoded value.
- Nested chain with env: `{{md5(env(secret_key))}}` → MD5 of environment variable value.

Invalid examples (kept as original text due fallback behavior):

- Unknown function: `{{not_allowed(db)}}`
- Unknown function nested: `{{md5(bad(db))}}`
- Multi-argument call: `{{urlencode(db, host)}}`
- Multi-argument inside nested call: `{{md5(urlencode(a, b))}}`
- Literal argument: `{{urlencode('db')}}`
- Literal inside nested call: `{{md5(urlencode('db'))}}`
- Malformed signature: `{{urlencode(db}}`
- Unsafe attribute path: `{{ db.__class__ }}`, `{{ mcp.request.__class__ }}`

### Invalid expression fallback

On validation or render failure, `render_string` returns the **original field content**
unchanged. This is intentional backward-compatible behavior — one bad expression must not
break unrelated fields or plain `{{var}}` placeholders. `HTTPClient` makes one
targeted exception for a failed direct `to_int(...)`; see [Strict HTTP failure
boundary](#strict-http-failure-boundary).

| Path | User-visible outcome | Diagnostics |
| --- | --- | --- |
| Runtime / hover outside strict HTTP conversion | Entire field kept as typed literal | `INFO` validation + `WARNING` fallback logs; `validation_error` metric |
| Strict HTTP direct `to_int(...)` failure | `ExecutionError(TEMPLATE)` and no outbound dispatch | `WARNING` template fallback plus safe HTTP `ERROR` event; existing template metrics |
| Hover preview | Tooltip shows original `{{...}}` token | Same render path with `render_path="hover"` |
| Render exception | Original content returned | `WARNING` fallback log; `render_error` metric (non-`ValueError` only) |

There is no inline error UI in PYPOST-450 scope. Structured codes appear in logs and
Prometheus labels via `TemplateService._VALIDATION_MESSAGES` (logging only).

Flow:

```text
validate_content → invalid? → log/metrics → raise ValueError inside try
render_with_jinja → exception? → log/metrics → except handler
except → return original content string unchanged
```

## Security

Function execution is restricted to the catalog in `FunctionRegistry`. Enforcement points:

1. `FunctionExpressionResolver` — grammar and catalog membership before render.
2. `FunctionRegistry.register_into_env` — only catalog keys bound to `env.globals`.
3. Jinja `Environment` — not a `SandboxedEnvironment`; security relies on allow-list +
   pre-render validation, not template sandboxing.

Rejected non-catalog Jinja constructs (original content returned):

- Jinja filters: `{{ db|md5 }}`
- Unsafe attribute paths with underscore-leading segments: `{{ db.__class__ }}`,
  `{{ mcp.request.__class__ }}`

Safe dotted paths (no underscore-leading attribute segments) are allow-listed and
rendered by Jinja against nested dicts — for example MCP
`{"mcp": {"request": {...}}}` from `_merge_execution_variables`. This is intentional
(PYPOST-1033); it does not open private-attribute access.

Negative / acceptance tests:

- `tests/test_template_service.py`: filter/attribute rejection; nested MCP render
  (`test_render_nested_mcp_request_variable`)
- `tests/test_function_expression_resolver.py`: safe MCP path acceptance; underscore
  segment locks (`test_validate_accepts_safe_mcp_request_path`)
- `tests/test_mcp_server_integration.py`:
  `test_call_tool_substitutes_mcp_request_path_placeholder`

## Nested Function Call Policy (PYPOST-453)

| Rule | Behavior |
|------|----------|
| Nested allow-listed calls | **Allowed** — argument is safe variable path or nested allow-listed call |
| Depth limit | **None** — each level must satisfy catalog + single-argument rules |
| Catalog check | `FunctionRegistry.is_allowed` at every call node, recursively |
| Multi-argument at any level | Rejected (`invalid_arity`; outer may see `invalid_argument`) |
| Literals / arbitrary expressions | Rejected (`invalid_argument` or `invalid_syntax`) |
| Unknown function in chain | Rejected (`unknown_function` on the offending name) |

Policy constant: `NESTED_FUNCTION_CALLS_ALLOWED = True` in
`pypost/core/function_expression_resolver.py`. It is **declarative** (documented intent);
validation logic does not branch on it in the current release.

**`function_name` on nested errors:** inner validation failures propagate with the
**innermost** offending function name (for example `urlencode` for
`{{md5(urlencode('db'))}}`, not `md5`). Only inner `invalid_arity` is remapped to outer
`invalid_argument`.

Edge-case acceptance tests for malformed nesting and spacing variants were added in
[PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454) — see **Edge-Case Expression
Variants (PYPOST-454)** below.

## Edge-Case Expression Variants (PYPOST-454)

PYPOST-454 closes PYPOST-450 missing-test debt with **tests-only** delivery. Acceptance
checks lock observed resolver and render behavior for malformed nested expressions,
whitespace-heavy variants, and runtime/hover parity. No production code changed.

### Malformed nested expressions (M1–M4)

Unbalanced or incomplete nesting at depth (not empty-argument or standalone
closing-paren patterns — see PYPOST-461 boundary below).

| ID | Example | Validation code | `function_name` | Render fallback |
| --- | --- | --- | --- | --- |
| M1 | `{{ md5(urlencode(db) }}` | `invalid_argument` | `md5` | original content |
| M2 | `{{ md5(urlencode(db))) }}` | `invalid_argument` | `urlencode` | original content |
| M3 | `{{ md5((urlencode(db))) }}` | `invalid_argument` | `md5` | original content |
| M4 | `{{ base64(md5(urlencode(db) }}` | `invalid_argument` | `base64` | original content |

Codes are **observed and locked** — the resolver surfaces malformed nesting as
`invalid_argument` with outer or inner `function_name` depending on where recursive
validation fails, not always `invalid_syntax`. Both `runtime` and `hover` render paths
return original content.

### Spacing variants (S1–S5)

Inner delimiter whitespace and argument spacing inside `{{ ... }}` are tolerated when the
grammar accepts the form. Space between function name and opening paren is rejected.

| ID | Example | Valid? | Validation code | `function_name` | Parity expectation |
| --- | --- | --- | --- | --- | --- |
| S1 | `{{  md5( db )  }}` | yes | valid | — | same hash as tight `{{md5(db)}}` |
| S2 | `{{  md5( urlencode( db ) )  }}` | yes | valid | — | same hash as tight nested form |
| S3 | `{{md5( urlencode(db))}}` | yes | valid | — | same hash as tight nested form |
| S4 | `{{ md5 ( urlencode ( db ) ) }}` | no | `invalid_syntax` | — | original content |
| S5 | `{{md5(urlencode (db))}}` | no | `invalid_argument` | `md5` | original content |

### Runtime / hover parity

Edge-case parity is proven at `TemplateService.render_string(..., render_path=...)`.
For each valid spaced row (S1–S3), `runtime` and `hover` produce identical resolved output.
For each malformed nested row (M1–M4) and invalid spacing row (S4–S5), both paths return
**original content** unchanged.

Table-cell tooltips delegate through `VariableAwareTableWidget` →
`VariableHoverHelper.resolve_text` → `TemplateService.render_string(...,
render_path="hover")`. No separate table parsing path; hover-parity at `TemplateService`
satisfies table-cell equivalence (PYPOST-453 precedent).

### Test coverage

**Resolver validation** (`tests/test_function_expression_resolver.py`):

- Catalog, nesting, multi-arg rejection, unknown functions
- `test_malformed_nested_expressions` — M1–M4 matrix
- `test_nested_spacing_variants` — S1–S5 matrix

**Unit tests — `TemplateService`** (`tests/test_template_service.py`, PYPOST-147,
PYPOST-145):

Isolated coverage for `pypost/core/template_service.py` (closes PYPOST-18 missing-test debt):

| Class | Public API / behavior |
| --- | --- |
| `TestTemplateServiceRenderString` | `render_string` — variables, catalog, nesting, fallback |
| `TestTemplateServiceVariableTypes` | `render_string` — int/float/bool/None variable values (PYPOST-145) |
| `TestTemplateServiceParse` | `parse` → Jinja AST |
| `TestTemplateServiceValidationOutcomes` | `validate_function_expressions` — codes, plain identifiers |
| `TestTemplateServiceObservability` | Metrics + `render_path` labels |
| `TestTemplateServiceRenderStages` | Staged render outcomes (incl. mocked render error) |
| `TestTemplateServiceHelperStages` | Fallback helper metrics branching |

Syntax/structure error fallback is covered by `TestTemplateServiceRenderString` and
`TestTemplateServiceValidationOutcomes` (PYPOST-147); PYPOST-145 adds variable-type gaps only.

Scoped run: 55 tests + subtests (2026-06-12).

**Render, parity, security, observability** (highlights within the file above):

- Catalog functions, nested chains, fallback on invalid forms
- Jinja filter/attribute rejection (security negatives)
- `test_runtime_hover_parity_*` — valid/malformed/spacing parity (runtime vs hover)
- `test_validate_malformed_nested_alignment` — resolver ↔ delegate codes for M1–M4
- Metrics tests for `success`, `validation_error`, and hover-path labels

**HTTPClient integration** (`tests/test_http_client.py`, class
`TestHTTPClientFunctionExpressions`):

| Test | Surface | What it proves |
| --- | --- | --- |
| `test_function_expression_substituted_in_url` | URL | `urlencode` in outbound URL |
| `test_function_expression_substituted_in_header_value` | Header value | `md5` in header |
| `test_function_expression_substituted_in_param_key_and_value` | Param key + value | `urlencode` key, `base64` value |
| `test_invalid_function_expression_passthrough_in_params` | Param key + value | Invalid expressions kept literal |

**Optional HTTPClient gaps** (same pipeline, thinner end-to-end coverage):

- Request body function expression through `HTTPClient.send_request`
- Header name (key column) function expression through HTTPClient

Body and header-name surfaces are covered at `TemplateService` and hover/widget layers.

**Hover widgets** (`tests/test_variable_hover.py`): URL, body, and table-cell tooltips.

Shared case data: `MALFORMED_NESTED_EXPRESSION_CASES` in
`tests/test_function_expression_resolver.py` (imported by `test_template_service.py`).

Full PYPOST-450 suite (STEP 6, 2026-06-06): 109 passed, 39 subtests across the files above.

### PYPOST-461 boundary (completed)

PYPOST-454 owns **nested-structure** malformation and **whitespace-heavy** variants plus
parity for those forms. [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461) closed
the remaining PYPOST-450 missing-test debt — see **Edge-Case Expression Variants
(PYPOST-461)** below.

## Edge-Case Expression Variants (PYPOST-461)

PYPOST-461 adds **tests-only** acceptance coverage for empty-argument calls, standalone
extra-closing-paren patterns, and multi-placeholder **first-failure** validation ordering.
No production code changed.

### Empty-argument calls (E1–E3)

Omitting the required single argument maps to `invalid_argument` (not `invalid_arity`) because
the empty argument string fails identifier and nested-call grammar checks.

| ID | Example | Validation code | `function_name` |
| --- | --- | --- | --- |
| E1 | `{{ md5() }}` | `invalid_argument` | `md5` |
| E2 | `{{ urlencode() }}` | `invalid_argument` | `urlencode` |
| E3 | `{{ base64() }}` | `invalid_argument` | `base64` |

### Standalone extra closing paren (P1–P2)

Top-level extra `)` (not primarily nested-structure malformation — see M1–M4 above):

| ID | Example | Validation code | `function_name` |
| --- | --- | --- | --- |
| P1 | `{{ urlencode(db)) }}` | `invalid_argument` | `urlencode` |
| P2 | `{{ md5(x)) }}` | `invalid_argument` | `md5` |

### First-failure validation ordering (F1–F5, V1–V2)

When content contains multiple `{{ ... }}` placeholders, validation scans placeholders
**left to right** (tokenization order) and returns the **first** failing expression.
Later placeholders are not evaluated once a failure is found.

`validate_content` tokenizes then delegates to `validate_expressions`. The render path uses
the same ordering after a single tokenization pass
(`TemplateService._validate_template_expressions`).

| ID | Example / expressions | First failure code | `function_name` |
| --- | --- | --- | --- |
| F1 | `{{ host }} {{ md5() }}` | `invalid_argument` | `md5` |
| F2 | `{{ urlencode(x) }} {{ mystery(y) }}` | `unknown_function` | `mystery` |
| F3 | `{{ mystery(y) }} {{ urlencode(x) }}` | `unknown_function` | `mystery` |
| F4 | `{{ md5(urlencode(db)) }} {{ md5() }}` | `invalid_argument` | `md5` |
| F5 | `{{ host }} {{ urlencode(a, b) }}` | `invalid_arity` | `urlencode` |
| V1 | `["host", "urlencode(x)", "mystery(y)"]` (`validate_expressions`) | `unknown_function` | `mystery` |
| V2 | `["md5(urlencode(db))", "md5()"]` via `validate_expressions` | `invalid_argument` | `md5` |

### Test coverage (PYPOST-461)

**Resolver validation** (`tests/test_function_expression_resolver.py`):

- `EMPTY_ARGUMENT_CASES` — E1–E3 (`test_empty_argument_calls`)
- `STANDALONE_MALFORMED_CLOSING_PAREN_CASES` — P1–P2
  (`test_standalone_malformed_closing_paren`)
- `MULTI_PLACEHOLDER_FIRST_FAILURE_CASES` — F1–F5 (`test_multi_placeholder_first_failure`)
- `test_multi_placeholder_first_failure_via_validate_expressions` — V1–V2 direct API contract

Malformed nested M1–M4 remain in `MALFORMED_NESTED_EXPRESSION_CASES` (PYPOST-454).

## Configuration

There are no end-user settings or environment variables for this feature in current scope.

Developer-facing configuration points:

- The default function catalog lives in `FunctionRegistry` (`pypost/core/function_registry.py`).
  To add or rename functions, extend the registry module and keep resolver expectations and
  `TemplateService` wiring in sync.
- Runtime observability is active when `TemplateService` is constructed with
  `metrics=MetricsManager` (wired in `pypost/main.py`).
- Hover-path observability is active when `VariableHoverHelper.set_metrics(metrics)` is called
  (wired from `RequestWidget` initialization).

Observability behavior:

- Logs from `TemplateService`:
  - `INFO`: validation failures (`render_path`, `code`, `function_name`, `token_count`)
  - `DEBUG`: successful render (`render_path`, `token_count`)
  - `WARNING`: fallback to original content (`render_path`, `error_type`, `token_count`)
- Metrics (Prometheus):
  - `template_expression_render_attempts_total{render_path,outcome}`
    - outcomes: `success`, `validation_error`, `render_error`, `empty_content`
  - `template_expression_validation_failures_total{render_path,code,function_name}`
- `FunctionExpressionResolver` remains observability-free by design; it returns structured
  `ValidationResult` only.

## Rendering Orchestration Stages (PYPOST-459)

`TemplateService.render_string()` delegates each stage to a private helper method. The stages
execute in this order:

| # | Helper | Responsibility |
|---|--------|---------------|
| 1 | `_record_empty_render_attempt()` | Short-circuit on empty content; emit `empty_content` metric |
| 2 | `tokenize_template_expressions()` | Single scan: token list and `token_count` for logs |
| 3 | `_validate_template_expressions()` | Delegate to `FunctionExpressionResolver.validate_expressions` |
| 4 | `_emit_validation_failure_observability()` | Log + emit `validation_error` metric on invalid input |
| 5 | `_render_with_jinja()` | Execute Jinja2 rendering with provided variables |
| 6 | `_emit_render_success_observability()` | Log + emit `success` metric on successful render |
| 7 | `_fallback_content_after_render_exception()` | On exception: emit `render_error` (non-ValueError only); return original content |

The following are intentionally unchanged by PYPOST-459 (parity contract):

- Metric names, outcome strings, and label values
- Log message formats and fields
- Fallback semantics: `ValueError` (from validation) does not emit `render_error`; all other
  exceptions do
- Token counting regex pattern: `\{\{\s*(.*?)\s*\}\}`
- `FunctionExpressionResolver` contract

## Known gaps and follow-ups

PYPOST-450 is functionally complete. Remaining items are maintainability and optional
hardening — not release blockers.

| Item | Jira | Notes |
| --- | --- | --- |
| Expression/template caching | — | Evaluated in PYPOST-455; deferred (see Caching evaluation) |
| Registry vs `env.globals` parity test | — | Done in PYPOST-457 (`test_function_registry`, `test_template_service`) |
| Shared tokenization dedup | — | Done in PYPOST-460 (`template_expression_tokenizer`) |
| Empty-arg / multi-placeholder / closing-paren edge cases | — | Done in PYPOST-461 (see PYPOST-461 section) |
| Hover regex vs resolver identifier rules | — | `PLAIN_VARIABLE_PATTERN` allows digit-leading names; resolver `_SAFE_PATH_RE` does not |
| Hover fast-path for dotted paths | — | `PLAIN_VARIABLE_PATTERN` is undotted; `{{ mcp.request.* }}` uses full `render_string` path |
| Plain variable pattern centralization | — | Done in PYPOST-113 (`PLAIN_VARIABLE_PATTERN` + helpers in tokenizer) |
| Hover expression pattern vs tokenizer | — | Done in PYPOST-536 (`EXPRESSION_PATTERN` aliases `TEMPLATE_PLACEHOLDER_PATTERN`) |
| HTTPClient body / header-name integration | — | Optional; shared `render_string` path already proven |
| Table tooltip malformed/spacing variants | — | Hover pipeline proven at `TemplateService`; table tests cover valid function cells only |
| Class-level hover `TemplateService` | — | `VariableHoverHelper` uses class-level instance via `set_metrics()` |

Completed follow-ups referenced in this doc: PYPOST-451 (registry), PYPOST-452 (resolver),
PYPOST-453 (nested policy), PYPOST-454 (edge-case tests), PYPOST-456 (doc polish),
PYPOST-457 (registry/globals parity test), PYPOST-459 (orchestration stage helpers in
`TemplateService`), PYPOST-460 (shared tokenization), PYPOST-461 (empty-arg / first-failure
tests), PYPOST-455 (caching evaluation), PYPOST-1033 (safe dotted variable paths for MCP
request substitution).

## Caching evaluation (PYPOST-455)

**Decision: defer implementation.** No render cache is active today.

### Current cost (local benchmark, 2026-06-11)

| Scenario | Approx. cost |
| --- | ---: |
| Plain two-placeholder template | ~130 µs/render |
| Single function expression | ~152 µs/render |
| Nested `base64(md5(...))` chain | ~182 µs/render |
| Simulated HTTP request (URL + headers + params + body) | ~0.7 ms/request |

Network I/O dominates request latency. PYPOST-460 already removed duplicate tokenization;
remaining repeatable work is `Environment.from_string` compile plus validation per call.

### Monitoring

Use existing Prometheus counters (no new metrics from PYPOST-455):

- `template_expression_render_attempts{render_path, outcome}`
- `template_expression_validation_failures{render_path, code, function_name}`

### Revisit criteria

Consider a compiled-template LRU (`functools.lru_cache` on compile, bounded `maxsize`) when:

- Users report hover lag with function templates, or
- Prometheus shows sustained very high render attempt rates, or
- Production templates routinely carry many placeholders (20+).

Guard tests for future cache work: `tests/test_template_service_caching_eval.py`.

Full analysis: `ai-tasks/PYPOST-455/20-architecture.md`.

## Troubleshooting

Expression does not render and stays unchanged:

- Check expression uses the canonical form: function name and argument inside `{{...}}`.
- Confirm function is allow-listed (`urlencode`, `md5`, `base64`) via `FunctionRegistry`.
- Confirm only one top-level argument is passed.
- Confirm argument is a safe variable path (plain identifier or dotted path per
  `_SAFE_PATH_RE`) or a nested allow-listed function expression.
- For MCP placeholders, confirm the path is `mcp.request.<param>` (no underscore-leading
  segments) and that execution variables include the nested `mcp.request` dict.

Hover tooltip differs from expectation:

- Ensure `RequestWidget` has called `VariableHoverHelper.set_metrics(...)` and variables are set.
- Plain hidden variables are masked; function-derived outputs are currently shown as resolved text.
- Digit-leading plain variables (for example `{{0db}}`) may resolve in hover via the fast
  lookup path but fail resolver validation at runtime — see Known gaps above.

Field unchanged after send but expression looks valid:

- Confirm the function name is in the catalog (`urlencode`, `md5`, `base64`).
- Check logs for `validation_error` with `code` and `function_name` labels.
- Multi-arg calls (`{{urlencode(a, b)}}`) and literal arguments (`{{urlencode('db')}}`)
  are rejected by design.

Need to inspect failures in detail:

- Check application logs for validation/fallback fields (`code`, `function_name`, `error_type`).
- Inspect Prometheus counters for `validation_error` and `render_error` outcomes.
- If behavior differs between runtime and hover, compare `render_path` labels in logs/metrics.
