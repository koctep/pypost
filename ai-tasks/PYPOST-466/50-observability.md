# PYPOST-466: Observability

## Events

The variable reorder operation logs a single event via `logger.info`:

```
env_variable_moved env_name=<name> key=<masked_or_plain> direction=up|down
```

- **Masking:** Uses the existing `HiddenToggleLogPolicy.format_key_name()` to ensure hidden keys are masked as `********` by default unless `log_hidden_key_names=True` is explicitly passed (matching the hidden-toggle and delete logic).
- **Values:** Variable values are not logged, maintaining secrets safety.

## Metrics

No new Datadog metrics were introduced. This is a local UI-only dialog action, comparable to renaming or deleting an environment variable.
