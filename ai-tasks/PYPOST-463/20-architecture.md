# PYPOST-463: History-recording helper extraction

## Research

The history block in `RequestService.execute` (post-PYPOST-446) performs four concerns:

1. Masked field resolution via `SensitiveDataMaskingPolicy`
2. `HistoryEntry` construction
3. Pre-append observability (masking debug log + metric)
4. Post-append observability (entry debug log + metric)

No new modules or classes are required; private instance methods on `RequestService` suffice.

## Implementation Plan

1. Add `_build_history_entry` — masking + `HistoryEntry` construction; returns entry and
   hidden-key count.
2. Add `_emit_history_masking_observability` — pre-append debug log and masking metric.
3. Add `_emit_history_entry_observability` — post-append debug log and append metric.
4. Add `_record_execution_history` — orchestrates the above with existing try/except guard.
5. Replace inline block in `execute()` with a single call to `_record_execution_history`.

## Architecture

```text
RequestService.execute()
  → _record_execution_history()
      → _build_history_entry()
      → _emit_history_masking_observability()
      → HistoryManager.append()
      → _emit_history_entry_observability()
```

| Method | Responsibility |
|--------|----------------|
| `_build_history_entry` | Mask fields and construct `HistoryEntry` |
| `_emit_history_masking_observability` | Debug log + `hidden_value_masks_applied_total` |
| `_emit_history_entry_observability` | Debug log + `history_entries_appended_total` |
| `_record_execution_history` | Guard, orchestrate, swallow errors |

## Q&A

- **Why not a separate class?** The logic is tightly coupled to `RequestService` state
  (`_masking_policy`, `_history_manager`, `_metrics`); private methods match project style.
