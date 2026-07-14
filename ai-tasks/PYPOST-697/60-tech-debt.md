# PYPOST-697: Architecture

## Plan

1. Add `VariableHoverResolver.set_template_service(template_service)`.
2. Call from `MainWindow.__init__` after composition-root service is stored.
3. Forward from `RequestWidget.set_template_service` (already invoked by `TabsPresenter`).
4. Remove `set_metrics` call from `RequestWidget.__init__` (was creating a second instance).
5. Keep `set_metrics` as deprecated helper for tests.

## Verdict

**SAFE TO CLOSE**
