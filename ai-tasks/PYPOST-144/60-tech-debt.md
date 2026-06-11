# PYPOST-144: Technical Debt Analysis

## Shortcuts Taken

- `HTTPClient` still auto-creates `TemplateService()` when `None` is passed (PYPOST-45
  default). Production always injects from `main.py`; tests may rely on the default.

## Code Quality Issues

- None blocking. Direct global import debt for `HTTPClient` and `MCPServerImpl` is closed.

## Performance Concerns

- None introduced.

## Follow-up Tasks

- **VariableHoverHelper class-level `TemplateService`**: `pypost/ui/widgets/mixins.py` still
  holds a class-level instance. Out of PYPOST-144 scope; consider UI-layer DI in a future
  ticket if hover/tooltip tests need shared mock injection.
