# PYPOST-109: Observability

## Logging

No new log events. Large paste uses the default Qt insert path.

## Metrics

No new metrics. Paste is synchronous UI behaviour; skipping parse avoids blocking but is not
tracked separately.

## User-visible behaviour

Large pastes insert raw clipboard text without pretty-print or JSON→YAML conversion. No error
dialog — behaviour matches non-JSON paste fallback.
