# PYPOST-913: Observability Implementation

## Logging Implementation

### Added Logs

None — provenance lives in `diagnostics.json` only.

### Changed Fields

- `diagnostics.json`: `session_fixture` → `session_source` (same values).

### Log Structure

Unchanged — dump success/failure log lines do not embed provenance.

## Metrics Implementation

N/A — field rename in on-disk diagnostics only.

## Monitoring Integration

N/A — CI artifact consumers read `diagnostics.json`; no new alerts.

## Validation Results

- [x] Contract test asserts `session_source` key and absence of `session_fixture`
- [x] Subprocess hook proofs assert updated key
- [x] No new log events

## Notes

Authors triaging dumps: read `session_source` in `diagnostics.json` (fixture
name or `direct`).
