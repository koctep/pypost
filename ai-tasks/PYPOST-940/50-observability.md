# PYPOST-940: Observability

## Scope

Test-harness only — no production logging or metrics changes.

## Notes

- Teardown helper runs synchronously during fixture `finally` blocks; no new
  DEBUG scalars required.
- Qt destructor warnings are the observability signal this task removes from
  ui_select fixture tests.

## Checklist

- [x] N/A for production observability documented
- [x] No new log/metric surface introduced
