# PYPOST-82: Observability

## Scope

Documentation-only task. No new logs, metrics, or tracing.

---

## Existing Coverage (unchanged)

The PYPOST-378 DI chain logs at `main.py` (INFO) and downstream consumers (DEBUG) already
let operators confirm a shared `TemplateService` instance in production. The new class docstring
references enabling `DEBUG` logging to verify identical `id()` values — it does not add new
instrumentation.

---

## Decision

No observability changes required for this ticket.
