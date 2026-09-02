# PYPOST-1244: Observability

Autocomplete trigger metrics and structured logs continue to report the configured context
and the number of displayed candidates. No variable values are added to the index, logs, or
metrics. The existing instrumentation therefore covers the new bounded lookup without adding
secret-bearing dimensions.

Validation includes the PYPOST-1244 focused tests and the repository lint/typecheck targets.
