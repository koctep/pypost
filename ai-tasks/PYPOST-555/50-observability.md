# PYPOST-555: Observability

## Logging

No new log lines required. The preview is a local, read-only UI computation with no runtime
server interaction.

## Metrics

No new Prometheus metrics. Operator contract inspection is a configuration-time UI action,
not a request/MCP execution event.

## Rationale

PYPOST-554 already logs execution-time merge counts at DEBUG. This task surfaces policy
outcomes in the UI instead of logs so operators do not need log access to verify exclusions.
