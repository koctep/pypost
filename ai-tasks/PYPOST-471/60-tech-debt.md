# PYPOST-471: Technical Debt

**Verdict:** SAFE TO CLOSE.

Shared `validate_variable_name` (PYPOST-478) adopted in `EnvironmentDialog.on_var_changed`
via `validate_environment_variable_name` in `environment_ops`.

## Follow-up Tasks

| Ticket | Description |
| --- | --- |
| [PYPOST-477](https://pypost.atlassian.net/browse/PYPOST-477) | Unit tests for validation helper |
| [PYPOST-497](https://pypost.atlassian.net/browse/PYPOST-497) | Further domain validation extraction |
