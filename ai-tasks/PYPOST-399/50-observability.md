# PYPOST-399: Observability

## Assessment

This task adds unit tests only. No runtime behavior, logging, or metrics paths change.

## Decision

**No new logging or metrics.**

| Criterion | Result |
| --------- | ------ |
| Critical execution path | Unchanged — tests exercise existing `highlightBlock` |
| Error conditions | None introduced |
| Performance | Test suite adds sub-second Qt offscreen cases |
| Existing metrics | N/A for test-only change |
