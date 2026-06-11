# Variable Validation

## Overview

PYPOST-163 adds validation for new variable names to ensure they are compatible with Jinja2
templating used throughout PyPost. Previously, only empty string validation was performed when
creating new environment variables via the context menu in the ResponseView.

## Why Variable Validation is Needed

Environment variables in PyPost are used as template variables in Jinja2 templates (for
request URLs, headers, body, etc.). Jinja2 on Python 3 follows Python identifier rules via
`str.isidentifier()` during tokenization. PyPost's validator uses `str.isalnum()` and
`str.isdigit()`, which are Unicode-aware but not identical to `isidentifier()`.

Practical rules enforced by PyPost:

- Must start with a letter or underscore (not a digit)
- Subsequent characters must be alphanumeric (`str.isalnum()`) or underscore
- Cannot be empty
- Cannot contain spaces, punctuation, emoji, or other non-alphanumeric characters (except `_`)

Without validation, users could create variable names that would cause template rendering
errors when used in requests. See [Unicode policy](#unicode-policy) for known divergences
between PyPost rules and strict Jinja2 identifier rules.

## Validation Rules

When creating a new variable name via the "New Variable..." option in the ResponseView context
menu (or editing keys in Manage Environments), the following rules are enforced:

1. **Not Empty**: Variable name cannot be empty after UI trimming (see
   [UI vs core behavior](#ui-vs-core-behavior))
   - Error: "Variable name cannot be empty."

2. **First Character**: Must be a letter or underscore (cannot start with a digit)
   - Uses `str.isdigit()` — Unicode decimal digits (for example fullwidth `１`, Arabic `٩`)
     are rejected at the start
   - Error: "Variable name cannot start with a digit."

3. **Subsequent Characters**: Each character must be `str.isalnum()` or `_`
   - Unicode letters are accepted (for example `café`, `变量`, `Ελληνικά`)
   - Combining marks, zero-width characters, emoji, and punctuation are rejected
   - Error: "Variable name can only contain letters, numbers, and underscores."

### Failure-reason precedence

The validator returns one canonical failure reason for metrics and logging. Order in
`validation_failure_reason()`:

1. `empty` — falsy string (`""`)
2. `starts_with_digit` — `name[0].isdigit()`
3. `invalid_chars` — any character not `isalnum()` and not `_`

When multiple violations apply (for example `9!`), `starts_with_digit` wins over
`invalid_chars`.

## Unicode Policy

PyPost accepts **Unicode letters** in variable names because `str.isalnum()` treats them as
alphanumeric. This is documented and tested in `tests/test_variable_name_validation.py`
(PYPOST-470).

| Category | Examples | Outcome | Failure reason |
| --- | --- | --- | --- |
| Unicode letters | `café`, `变量`, `über`, `naïve`, `Ελληνικά` | Accept | — |
| Underscore + Unicode | `_变量`, `api_über` | Accept | — |
| Unicode digit start | `１abc`, `٩test` | Reject | `starts_with_digit` |
| Emoji / symbols | `api🔑`, `key❤`, `café!` | Reject | `invalid_chars` |
| Invisible / format chars | `api\u200bkey`, `soft\u00adhyphen` | Reject | `invalid_chars` |

**Jinja2 divergence (known, not fixed in PYPOST-470):** `isalnum()` and `isidentifier()` differ
on some edge cases. For example, `x²` may pass PyPost validation but fail Jinja2 tokenization,
while NFD forms with combining marks may fail PyPost but be valid identifiers. Aligning rules
to `isidentifier()` is a separate product decision; see PYPOST-470 tech-debt follow-ups.

## UI vs Core Behavior

The core module (`validate_variable_name`) receives the raw string and does **not** strip
whitespace.

| Layer | Whitespace handling | Empty check |
| --- | --- | --- |
| Core (`variable_name_validation.py`) | No strip; `" "` / `"\t"` → `invalid_chars` | Only `""` → `empty` |
| ResponseView (`EnvPresenter`) | `text.strip()` before validation | Stripped empty → UI empty warning |
| Manage Environments (`environment_ops`) | Caller strips before validation | Stripped empty → separate message |

Boundary tests pass whitespace-only strings directly into the core module to document
validator semantics. End-user dialogs strip input first, so a whitespace-only dialog entry
typically surfaces the empty-name path, not `invalid_chars`.

## Implementation Details

### Location

- **Rule source (shared):** `pypost/core/variable_name_validation.py`
  - `validate_variable_name(name) -> tuple[bool, str]` — pure validation, no side effects
  - `validation_failure_reason(name) -> ValidationFailureReason | None` — metric key mapping
- **UI integration:** `pypost/ui/presenters/env_presenter.py`
  - `EnvPresenter.handle_variable_set_request()` — new-variable flow
  - `EnvPresenter._is_valid_variable_name()` — delegates to core module; records metrics/logs
- **Manage Environments:** `pypost/core/environment_ops.py`
  - `validate_environment_variable_name()` — thin wrapper around core validation

### Flow

1. User right-clicks in ResponseView → Context Menu → "Set Variable" → "New Variable..."
2. QInputDialog prompts for variable name
3. On OK, the name is stripped and validated:
   - Empty check (existing)
   - Character validation (new)
4. If valid: Variable is created in current environment
5. If invalid: QMessageBox shows error, operation aborted

### Observability

- **Logging**: DEBUG logs for validation attempts, INFO logs for successful variable setting
- **Metrics**:
  - `gui_variable_validation_total{result="valid|invalid"}` — tracks validation attempts
  - `gui_variable_validation_failures_total{reason="empty|starts_with_digit|invalid_chars"}`
    — tracks failures by reason

## Examples

### Valid Variable Names

- `api_key`
- `_internal`
- `userId123`
- `service_url`
- `DEBUG_MODE`
- `café`, `变量`, `über` (Unicode letters)
- `naïve`, `Ελληνικά`, `变量名`
- `___`, `____` (underscore-only)
- `"a" * 500`, `"_" + "x" * 999` (long names)

### Invalid Variable Names

- `123api`, `0_` (starts with digit)
- `１abc`, `٩test` (Unicode digit start)
- `api-key`, `valid-name` (contains hyphen)
- `user name`, `a b` (contains space)
- `user.name` (contains period)
- `api key!`, `api_key!`, `letter1@domain` (illegal symbols)
- `api🔑`, `key❤`, `café!` (emoji or punctuation)
- `""` (empty string)
- `" "`, `"\t"` (whitespace-only at core layer; see UI vs core behavior)

## Test Coverage

Automated contract tests live in `tests/test_variable_name_validation.py`:

| Class | Scope |
| --- | --- |
| `TestValidateVariableName` | Baseline valid/invalid names (PYPOST-477) |
| `TestValidateVariableNameUnicode` | Unicode accept/reject matrix (PYPOST-470) |
| `TestValidateVariableNameMixed` | Mixed strings + canonical failure reason |
| `TestValidateVariableNameBoundaries` | Underscore-only, long names, whitespace-only |

Run focused tests:

```bash
.venv/bin/python -m pytest tests/test_variable_name_validation.py -v
```

## Troubleshooting

**Docs said ASCII-only but Unicode names work.** The validator uses `str.isalnum()`, which
accepts Unicode letters. PYPOST-470 reconciled documentation with tested behavior.

**Whitespace-only name rejected with wrong message in tests.** Core validation maps
whitespace-only input to `invalid_chars`. UI flows strip first and show the empty-name error
instead.

**Name passes validation but Jinja2 fails at render time.** Check for `isalnum()` vs
`isidentifier()` divergence (for example superscripts or combining marks). File a follow-up
if product policy should tighten rules.

**Mixed violation reports unexpected failure reason.** Verify precedence: digit-start beats
invalid characters (`9!` → `starts_with_digit`).

## Backward Compatibility

This change only affects *new* variable creation. Existing environment variables with any
naming convention continue to work unchanged. The validation is applied only when users
attempt to create new variables via the UI.

## Related Components

- `ResponseView` (`pypost/ui/widgets/response_view.py`) — Triggers the variable setting flow
- `TabsPresenter` (`pypost/ui/presenters/tabs_presenter.py`) — Routes variable_set_requested
  signal
- `MainWindow` (`pypost/ui/main_window.py`) — Sets up signal connections
- `MetricsManager` (`pypost/core/metrics.py`) — Tracks validation metrics
