# PYPOST-124: Observability

## Assessment

`JsonHighlighter` is a synchronous UI paint-path helper invoked on every document block
during edit/rehighlight. It performs regex scans only — no I/O, no network, no persistence.

## Decision

**No new logging or metrics** for this task.

| Criterion | Result |
| --------- | ------ |
| Critical execution path | UI rendering only; failures surface as missing colors, not crashes |
| Error conditions | None introduced; invalid JSON still highlights heuristically |
| Performance | O(rules × line length) per block — same order as existing rules + one extra pass |
| Existing metrics | Template/hover metrics remain in `VariableHoverHelper` / `TemplateService` |

## Notes

If editor performance becomes an issue on very large JSON bodies, consider profiling
`highlightBlock` collectively with hover regex scans ([PYPOST-120](https://pypost.atlassian.net/browse/PYPOST-120)).
