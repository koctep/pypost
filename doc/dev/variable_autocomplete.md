# Reusable Variable Autocomplete (PYPOST-1243)

## Overview

PyPost provides one variable-reference completion experience for request editors. It helps
users author `{{ VAR }}` references using names from the active environment while leaving
variable resolution and request construction to the existing services.

The capability is available in:

- Query-parameter value cells.
- Request-header value cells, including MCP server custom headers through the compatibility
  layer.
- Multiline request bodies at the current text cursor.

Completion exposes variable names only. It never displays or inserts environment values.

## Architecture

The shared implementation is in
`pypost/ui/widgets/variable_autocomplete_line_edit.py`:

- `VariableAutocompleteLineEdit` is a `QLineEdit` with a popup that detects `{{`, filters
  names case-insensitively, and supports keyboard or mouse selection.
- `VariableAutocompleteDelegate` creates the line editor for configured table value columns,
  bridges Qt model data, and refreshes editors that are currently open.
- `reference_statuses(text, names)` classifies empty, unfinished, and unavailable references
  without resolving their values.

Table hosts use the delegate while retaining ownership of row editing, serialization, and
validation. `CodeEditor` implements the equivalent multiline contract: it finds the trigger
before the cursor and replaces only that range with a formatted reference. Body formatting,
folding, syntax validation, and persistence remain owned by `CodeEditor`.

The old MCP import path re-exports the shared classes so existing integrations continue to
work. New hosts should import from the shared module instead.

## Usage and integration

### Table value editors

Install the delegate on the value column and provide an
`environment_variable_names` sequence (or a `variable_names()` provider):

```python
self._delegate = VariableAutocompleteDelegate(
    self,
    value_columns=(1,),
    context="query",
)
self.setItemDelegateForColumn(1, self._delegate)
```

Push the current environment snapshot into the table with `set_variables(variables)`. The
table updates its delegate and any existing editors, so an open popup reflects the new names.

### Body editor

`CodeEditor` accepts the same name/value snapshot through `set_variables(variables)`. Its
completion result has the shape `(start, end, replacement)` and is applied at the current
`QTextCursor` position. This preserves text before and after the trigger, including multiline
body content and multiple references.

### Feedback

Hosts call `reference_statuses()` when content or the environment changes. Statuses are
published as visible tooltip/feedback state:

- `empty`: the reference has no variable name.
- `incomplete`: the closing `}}` is missing.
- `unavailable`: the name is not present in the active environment.

Feedback identifies the problem without exposing a resolved value. These states are advisory;
existing host-specific structural validation and save rules still apply.

## Environment refresh and safe variables

Environment updates flow from `EnvPresenter` through `TabsPresenter` and request-editor
composites. Widgets receive snapshots through `set_variables()` and hidden-key metadata
through `set_hidden_keys()`; widgets do not subscribe directly to presenter signals.

Variable names are used for completion. Values remain in the existing hover/resolution path,
where `hidden_keys` prevents sensitive values from appearing in tooltips. Snapshot and masking
updates clear hover caches and revalidate visible references. Do not pass values to completion
popups, feedback messages, structured log fields, or metric labels.

There are no new settings or environment variables to configure. The active environment is the
only source of candidates.

## Observability

Autocomplete emits structured events using the `variable_autocomplete_*` event names. The
Prometheus registry and OpenTelemetry tracker record these counters:

- `gui_variable_autocomplete_triggers_total`, labelled by `context`.
- `gui_variable_autocomplete_selections_total`, labelled by `context`.
- `gui_variable_autocomplete_feedback_total`, labelled by `context` and status.
- `gui_variable_autocomplete_environment_refreshes_total`, labelled by `context`.

Logs may include context, candidate counts, prefixes, and variable names for compatibility, but
must not include variable values or other secret material.

## Troubleshooting

### No suggestions appear

Confirm that the active environment contains the expected variable name and that the host has
received `set_variables()`. Completion starts only when the text immediately before the cursor
matches `{{` plus an optional identifier prefix.

### Existing text is not refreshed after an environment switch

Check that the environment snapshot is pushed through the presenter/composite path and that
the host implements both `set_variables()` and `set_hidden_keys()`. Existing table editors are
refreshed by `VariableAutocompleteDelegate.set_variables()`.

### A reference is marked unavailable

The reference name is absent from the current environment snapshot. Select or update the
appropriate environment; the request text is intentionally preserved until the user edits it.

### A sensitive value is visible

Do not add value resolution to autocomplete. Verify that the environment key is included in
`hidden_keys` and that the existing hover resolver is receiving the updated masking snapshot.

## Related documentation

- [Environment variable propagation](variable_propagation.md)
- [Sensitive data masking policy](sensitive_data_masking_policy.md)
- [MCP server headers editor](mcp_server_headers_editor.md)
- [Metrics and observability](observability_audit.md)
