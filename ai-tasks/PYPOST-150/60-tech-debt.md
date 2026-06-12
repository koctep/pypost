# PYPOST-150: Technical Debt Analysis

## Shortcuts Taken

- `lsof` listen-address assertion is skipped when the tool is unavailable; TCP connect
  remains the minimum bar.

## Code Quality Issues

None blocking.

## Missing Tests

- External-network bind verification (e.g. LAN IP) not covered — requires environment-specific
  interfaces.

## Performance Concerns

None — tests start/stop uvicorn once per case with bounded waits.

## Follow-up Tasks

None required for close.
