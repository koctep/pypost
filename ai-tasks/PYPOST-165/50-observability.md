# PYPOST-165: Observability

## Assessment

No new metrics or log lines added. Invalid-name attempts in Manage Environments remain
client-side rejections without Prometheus counters (same as pre-change).

## Existing Coverage

- `EnvPresenter` new-variable flow: `gui_variable_validation_*` metrics and DEBUG logs.
- Manage Environments table: silent revert only (no metrics) — unchanged scope.

## Follow-up

Consider adopting `EnvPresenter`-style validation metrics for the env dialog in a separate
debt task if product wants parity.
