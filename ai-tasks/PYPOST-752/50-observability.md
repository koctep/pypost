# PYPOST-752: Observability

T201 enforces the logging convention documented in `doc/dev/logging.md`: application code in
`pypost/` must not emit diagnostics via stdout `print()`.

Lint failure message (`T201 print found`) surfaces at `make lint` / CI before merge.
