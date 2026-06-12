# PYPOST-151: Technical Debt Analysis

## Shortcuts Taken

- Hostname validation uses a pragmatic label regex rather than full IDNA/punycode or DNS
  lookup. Internationalized domain names are not specially handled.

## Code Quality Issues

None blocking. Validation mirrors existing retry-codes pattern.

## Missing Tests

- No automated test that uvicorn actually binds to saved host (tracked as
  [PYPOST-150](https://pypost.atlassian.net/browse/PYPOST-150)).
- Port conflict when MCP and metrics share host+port not validated.

## Performance Concerns

None — validation runs once per Save click.

## Follow-up Tasks

None required for close. PYPOST-149 is duplicate of this work — close as duplicate.
