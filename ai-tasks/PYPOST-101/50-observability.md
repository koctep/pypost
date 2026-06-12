# PYPOST-101: Observability

## Assessment

`JsonHighlighter` remains a synchronous UI paint-path helper. The new guard is a constant-time
length check before regex work — no I/O or persistence.

## Decision

**No new logging or metrics.**

| Criterion | Result |
| --------- | ------ |
| Critical path | UI rendering; skip path is silent by design |
| Error conditions | None; oversized blocks show uncolored plain text |
| Performance | Worst case avoided: no regex on blocks > 32 KiB |
| Existing metrics | Unchanged |

## Notes

If users report missing colors on very long single-line JSON, verify block length against
`MAX_HIGHLIGHT_BLOCK_CHARS` in `json_highlighter.py` before profiling regex cost.
