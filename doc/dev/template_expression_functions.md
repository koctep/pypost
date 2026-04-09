# Template Expression Functions (PYPOST-450)

## Overview

PYPOST-450 adds function expressions to template placeholders in all variable-enabled request
surfaces. Canonical syntax: function calls appear only inside `{{...}}`, for example
`{{urlencode(db)}}`.

Implemented behavior is backward compatible:

- Valid expressions are rendered through `TemplateService`.
- Invalid expressions fall back to original content (no hard request-time failure).
- Plain variable placeholders like `{{host}}` continue to work unchanged.

## Architecture

Main components:

- `pypost/core/template_service.py`
  - Owns expression validation and render execution.
  - Registers allow-listed functions in Jinja globals: `urlencode`, `md5`, `base64`.
  - Supports one top-level argument per function and allows nested function expressions.
- `pypost/ui/widgets/mixins.py` (`VariableHoverHelper`)
  - Reuses `TemplateService.render_string(..., render_path="hover")` for function hover parity.
  - Keeps hidden-variable masking for plain variables via `HIDDEN_MASK`.
- `pypost/core/metrics.py` (`MetricsManager`)
  - Exposes counters for expression render attempts and validation failures.

Current allow-list and validation rules are implemented inside `TemplateService` as
`_ALLOWED_FUNCTIONS` plus parser/validator helpers (not yet extracted into a separate registry).

### Known Deviation

- Current implementation allows nested function calls (for example `{{md5(urlencode(db))}}`).
- Architecture notes previously marked nested calls as out of scope for this iteration.
- Follow-up alignment task: [PYPOST-453](https://pypost.atlassian.net/browse/PYPOST-453).

## Usage

Supported patterns:

- Plain variable: `{{host}}`
- Function call: `{{urlencode(db)}}`
- Nested function call (currently implemented): `{{md5(urlencode(db))}}`

Supported functions:

- `urlencode(var)` -> URL-encoded string
- `md5(var)` -> hex MD5 digest
- `base64(var)` -> Base64-encoded string

Examples:

- URL field: `/{{host}}/{{urlencode(db)}}`
- Header/param/body values: `{{md5(secret)}}`, `{{base64(path)}}`
- Hover tooltip resolution uses the same render rules as runtime for function placeholders.

Invalid examples (kept as original text due fallback behavior):

- Unknown function: `{{not_allowed(db)}}`
- Multi-argument call: `{{urlencode(db, host)}}`
- Literal argument: `{{urlencode('db')}}`
- Malformed signature: `{{urlencode(db}}`

## Configuration

There are no end-user settings or environment variables for this feature in current scope.

Developer-facing configuration points:

- Function catalog is hardcoded in `TemplateService._ALLOWED_FUNCTIONS`.
- Runtime observability is active when `TemplateService` is constructed with
  `metrics=MetricsManager` (wired in `pypost/main.py`).
- Hover-path observability is active when `VariableHoverHelper.set_metrics(metrics)` is called
  (wired from `RequestWidget` initialization).

Observability additions:

- Logs (TemplateService):
  - `INFO`: validation failures (`render_path`, `code`, `function_name`, `token_count`)
  - `DEBUG`: successful render (`render_path`, `token_count`)
  - `WARNING`: fallback to original content (`render_path`, `error_type`, `token_count`)
- Metrics (Prometheus):
  - `template_expression_render_attempts_total{render_path,outcome}`
    - outcomes: `success`, `validation_error`, `render_error`, `empty_content`
  - `template_expression_validation_failures_total{render_path,code,function_name}`

## Troubleshooting

Expression does not render and stays unchanged:

- Check expression uses the canonical form: function name and argument inside `{{...}}`.
- Confirm function is allow-listed (`urlencode`, `md5`, `base64`).
- Confirm only one top-level argument is passed.
- Confirm argument is an identifier or a nested allow-listed function expression.

Hover tooltip differs from expectation:

- Ensure `RequestWidget` has called `VariableHoverHelper.set_metrics(...)` and variables are set.
- Plain hidden variables are masked; function-derived outputs are currently shown as resolved text.

Need to inspect failures in detail:

- Check application logs for validation/fallback fields (`code`, `function_name`, `error_type`).
- Inspect Prometheus counters for `validation_error` and `render_error` outcomes.
