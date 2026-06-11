# PYPOST-515: Observability

## Logging

No new log events. Paste conversion is synchronous UI behavior; failures fall back to default
paste (non-JSON) or use existing JSON parse path.

## Metrics

No new GUI metrics. Paste is not tracked separately; send-time conversion metrics from PYPOST-514
are unchanged.

## User-visible errors

Invalid JSON paste does not surface an error — text is inserted via default paste, matching prior
`CodeEditor` behavior.
